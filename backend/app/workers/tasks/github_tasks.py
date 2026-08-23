"""GitHub repository indexing worker."""
import asyncio
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def index_repository(self, repo_id: str):
    try:
        asyncio.run(_index_repo_async(repo_id))
    except Exception as exc:
        self.retry(exc=exc)


async def _index_repo_async(repo_id: str):
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    from app.models.github import GitHubRepository
    from app.ai.pipeline.chunker import chunk_text
    from app.ai.pipeline.indexer import ensure_collection, upsert_chunks
    from app.ai.embeddings.embedder import get_embedder
    from github import Github
    import datetime

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        result = await db.execute(select(GitHubRepository).where(GitHubRepository.id == repo_id))
        repo = result.scalar_one_or_none()
        if not repo:
            return

        repo.sync_status = "syncing"
        await db.commit()

        try:
            # Initialize GitHub client
            token = repo.access_token_encrypted  # TODO: decrypt
            gh = Github(token) if token else Github()
            gh_repo = gh.get_repo(repo.full_name)

            # Update repo metadata
            repo.github_repo_id = gh_repo.id
            repo.description = gh_repo.description
            repo.html_url = gh_repo.html_url
            repo.language = gh_repo.language
            repo.default_branch = gh_repo.default_branch_name

            documents_to_index = []

            # Index README
            if repo.index_readme:
                try:
                    readme = gh_repo.get_readme()
                    documents_to_index.append({
                        "path": "README.md",
                        "content": readme.decoded_content.decode("utf-8", errors="replace"),
                        "type": "readme",
                    })
                except Exception:
                    pass

            # Index /docs directory
            if repo.index_docs:
                try:
                    contents = gh_repo.get_contents("docs")
                    while contents:
                        item = contents.pop(0)
                        if item.type == "dir":
                            contents.extend(gh_repo.get_contents(item.path))
                        elif item.name.endswith((".md", ".rst", ".txt")):
                            documents_to_index.append({
                                "path": item.path,
                                "content": item.decoded_content.decode("utf-8", errors="replace"),
                                "type": "docs",
                            })
                except Exception:
                    pass

            # Embed and index all content
            if documents_to_index:
                embedder = get_embedder()
                workspace_id = str(repo.workspace_id)
                ensure_collection(workspace_id, embedder.dimensions)

                for doc_info in documents_to_index:
                    chunks = chunk_text(doc_info["content"], "markdown")
                    if not chunks:
                        continue

                    texts = [c["content"] for c in chunks]
                    embeddings = await embedder.embed_documents(texts)

                    metadata = {
                        "title": doc_info["path"],
                        "file_type": "markdown",
                        "file_name": doc_info["path"],
                        "source_type": "github",
                        "github_repo": repo.full_name,
                        "tags": ["github", repo.language or "unknown"],
                    }

                    upsert_chunks(workspace_id, f"github:{repo_id}:{doc_info['path']}", chunks, embeddings, metadata)

            repo.sync_status = "synced"
            repo.last_synced_at = datetime.datetime.now(datetime.timezone.utc)
            await db.commit()

        except Exception as e:
            repo.sync_status = "failed"
            await db.commit()
            raise

    await engine.dispose()
