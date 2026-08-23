"""Qdrant indexing: create collections and upsert document chunks."""
import uuid
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    OptimizersConfigDiff, HnswConfigDiff
)

from app.core.config import settings
from app.ai.embeddings.embedder import get_embedder


def collection_name(workspace_id: str) -> str:
    return f"workspace_{workspace_id.replace('-', '_')}"


def get_sync_client() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY or None)


def ensure_collection(workspace_id: str, vector_size: int):
    """Create Qdrant collection for workspace if it doesn't exist."""
    client = get_sync_client()
    coll = collection_name(workspace_id)

    existing = [c.name for c in client.get_collections().collections]
    if coll not in existing:
        client.create_collection(
            collection_name=coll,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
            optimizers_config=OptimizersConfigDiff(indexing_threshold=10000),
        )


def upsert_chunks(
    workspace_id: str,
    document_id: str,
    chunks: List[dict],
    embeddings: List[List[float]],
    document_metadata: dict,
):
    """Upsert embedded chunks into Qdrant collection."""
    if not chunks or not embeddings:
        return

    client = get_sync_client()
    coll = collection_name(workspace_id)

    points = []
    for chunk, embedding in zip(chunks, embeddings):
        point_id = str(uuid.uuid4())
        payload = {
            "chunk_id": point_id,
            "document_id": document_id,
            "workspace_id": workspace_id,
            "chunk_index": chunk.get("chunk_index", 0),
            "content": chunk.get("content", ""),
            "token_count": chunk.get("token_count", 0),
            "page_number": chunk.get("page_hint"),
            # Document metadata
            "title": document_metadata.get("title", ""),
            "file_type": document_metadata.get("file_type", ""),
            "file_name": document_metadata.get("file_name", ""),
            "author": document_metadata.get("author", ""),
            "tags": document_metadata.get("tags", []),
            "source_type": document_metadata.get("source_type", "document"),
            "github_repo": document_metadata.get("github_repo"),
            "language": document_metadata.get("language"),
        }

        points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

    # Batch upsert
    batch_size = 100
    for i in range(0, len(points), batch_size):
        client.upsert(collection_name=coll, points=points[i:i + batch_size])

    return [p.id for p in points]


def delete_document_chunks(workspace_id: str, document_id: str):
    """Remove all chunks for a document from Qdrant."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    client = get_sync_client()
    coll = collection_name(workspace_id)

    try:
        client.delete(
            collection_name=coll,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            ),
        )
    except Exception:
        pass  # Collection might not exist
