"""Document processing pipeline: extract → chunk → embed → index."""
import asyncio
import datetime
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: str):
    """Full document ingestion pipeline."""
    try:
        asyncio.run(_process_document_async(document_id))
    except Exception as exc:
        self.retry(exc=exc)


async def _process_document_async(document_id: str):
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    from app.models.document import Document, DocumentChunk
    from app.services.storage_service import StorageService
    from app.ai.pipeline.extractor import extract_text
    from app.ai.pipeline.chunker import chunk_text
    from app.ai.pipeline.indexer import ensure_collection, upsert_chunks
    from app.ai.embeddings.embedder import get_embedder
    import uuid

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        # Fetch document
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            return

        try:
            # Update status
            doc.processing_status = "processing"
            await db.commit()

            # Download from storage
            storage = StorageService()
            content = await storage.download_bytes(doc.storage_key)

            # Extract text
            text, metadata = extract_text(content, doc.file_type, doc.file_name)
            if not text.strip():
                raise ValueError("No text could be extracted from document")

            # Merge extracted metadata
            doc.doc_metadata = {
                **doc.doc_metadata,
                "extracted_title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "page_count": metadata.get("page_count"),
                "word_count": len(text.split()),
            }

            # Chunk
            chunks = chunk_text(text, doc.file_type)
            if not chunks:
                raise ValueError("Document produced no chunks")

            # Embed
            embedder = get_embedder()
            texts = [c["content"] for c in chunks]
            embeddings = await embedder.embed_documents(texts)

            # Ensure Qdrant collection exists
            workspace_id = str(doc.workspace_id)
            ensure_collection(workspace_id, embedder.dimensions)

            # Upsert to Qdrant
            doc_metadata = {
                "title": doc.title,
                "file_type": doc.file_type,
                "file_name": doc.file_name,
                "author": metadata.get("author", ""),
                "tags": doc.tags,
                "source_type": "document",
            }
            point_ids = upsert_chunks(workspace_id, str(doc.id), chunks, embeddings, doc_metadata)

            # Store chunk records in PostgreSQL
            for i, chunk in enumerate(chunks):
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    workspace_id=doc.workspace_id,
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    token_count=chunk["token_count"],
                    qdrant_point_id=uuid.UUID(point_ids[i]) if i < len(point_ids) else None,
                    page_number=chunk.get("page_hint"),
                    created_at=datetime.datetime.now(datetime.timezone.utc),
                )
                db.add(db_chunk)

            # Update document status
            doc.processing_status = "completed"
            doc.chunk_count = len(chunks)
            doc.embedding_model = type(embedder).__name__
            await db.commit()

            # Notify user via WebSocket (TODO: implement WebSocket notifier)

        except Exception as e:
            doc.processing_status = "failed"
            doc.processing_error = str(e)[:500]
            await db.commit()
            raise

    await engine.dispose()


@celery_app.task
def cleanup_expired_tokens():
    """Periodic task: remove expired refresh tokens."""
    asyncio.run(_cleanup_tokens())


async def _cleanup_tokens():
    from sqlalchemy import delete
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    from app.models.user import RefreshToken
    import datetime

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        await db.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < datetime.datetime.now(datetime.timezone.utc))
        )
        await db.commit()

    await engine.dispose()
