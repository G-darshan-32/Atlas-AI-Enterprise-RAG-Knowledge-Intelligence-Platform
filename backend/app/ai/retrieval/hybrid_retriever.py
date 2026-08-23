from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
from rank_bm25 import BM25Okapi
from typing import Optional
import numpy as np

from app.ai.embeddings.embedder import get_embedder
from app.core.config import settings


def collection_name(workspace_id: str) -> str:
    return f"workspace_{workspace_id.replace('-', '_')}"


def reciprocal_rank_fusion(dense_results: list, sparse_results: list, k: int = 60) -> list:
    """Merge dense and sparse rankings using RRF."""
    scores: dict[str, float] = {}
    doc_map: dict[str, dict] = {}

    for rank, doc in enumerate(dense_results):
        doc_id = doc["chunk_id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = doc

    for rank, doc in enumerate(sparse_results):
        doc_id = doc["chunk_id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = doc

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for doc_id, rrf_score in ranked:
        doc = doc_map[doc_id].copy()
        doc["score"] = round(rrf_score * 100, 4)  # scale for readability
        results.append(doc)

    return results


class HybridRetriever:
    def __init__(self):
        self.qdrant = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
        )
        self.embedder = get_embedder()

    async def search(
        self,
        query: str,
        workspace_id: str,
        filters: Optional[dict] = None,
        top_k: int = 8,
    ) -> list[dict]:
        coll = collection_name(workspace_id)

        # Check if collection exists
        try:
            collections = await self.qdrant.get_collections()
            existing = [c.name for c in collections.collections]
            if coll not in existing:
                return []
        except Exception:
            return []

        # Generate query embedding
        query_vector = await self.embedder.embed_query(query)

        # Build Qdrant filter
        qdrant_filter = self._build_filter(workspace_id, filters)

        # Dense retrieval
        dense_results = await self._dense_search(coll, query_vector, qdrant_filter, top_k * 5)

        # Sparse retrieval (BM25 over retrieved content)
        sparse_results = self._sparse_rerank(query, dense_results[:50])

        # Fuse
        fused = reciprocal_rank_fusion(dense_results[:20], sparse_results[:20])

        # Cross-encoder re-ranking on top candidates
        top_candidates = fused[:min(10, len(fused))]
        reranked = await self._cross_encoder_rerank(query, top_candidates)

        return reranked[:top_k]

    async def _dense_search(self, collection: str, vector: list, qdrant_filter, limit: int) -> list[dict]:
        try:
            results = await self.qdrant.search(
                collection_name=collection,
                query_vector=vector,
                query_filter=qdrant_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            return [
                {
                    "chunk_id": str(r.id),
                    "score": r.score,
                    **r.payload,
                }
                for r in results
            ]
        except Exception:
            return []

    def _sparse_rerank(self, query: str, candidates: list[dict]) -> list[dict]:
        if not candidates:
            return []

        corpus = [c.get("content", "").split() for c in candidates]
        if not any(corpus):
            return candidates

        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(query.split())

        ranked = sorted(
            zip(candidates, scores),
            key=lambda x: x[1],
            reverse=True
        )
        return [doc for doc, _ in ranked]

    async def _cross_encoder_rerank(self, query: str, candidates: list[dict]) -> list[dict]:
        """Re-rank with cross-encoder if available, otherwise return as-is."""
        try:
            from sentence_transformers import CrossEncoder
            model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            pairs = [(query, c.get("content", "")) for c in candidates]
            scores = model.predict(pairs)
            ranked = sorted(
                zip(candidates, scores),
                key=lambda x: float(x[1]),
                reverse=True
            )
            for doc, score in ranked:
                doc["rerank_score"] = float(score)
            return [doc for doc, _ in ranked]
        except Exception:
            return candidates

    def _build_filter(self, workspace_id: str, filters: Optional[dict]) -> Optional[Filter]:
        conditions = [
            FieldCondition(key="workspace_id", match=MatchValue(value=workspace_id))
        ]

        if filters:
            if "file_type" in filters:
                ft = filters["file_type"]
                if isinstance(ft, list):
                    conditions.append(FieldCondition(key="file_type", match=MatchAny(any=ft)))
                else:
                    conditions.append(FieldCondition(key="file_type", match=MatchValue(value=ft)))

            if "source_type" in filters:
                conditions.append(
                    FieldCondition(key="source_type", match=MatchValue(value=filters["source_type"]))
                )

            if "document_id" in filters:
                conditions.append(
                    FieldCondition(key="document_id", match=MatchValue(value=filters["document_id"]))
                )

        return Filter(must=conditions) if conditions else None
