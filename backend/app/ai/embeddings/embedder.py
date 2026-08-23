"""Embedding models — uses the local BGE sentence-transformer (no OpenAI/Groq API needed).

Groq does not provide an embeddings API. The local BAAI/bge-large-en-v1.5 model
is used for all vector embedding operations (zero API cost, runs offline).
"""
from typing import List
from app.core.config import settings


class LocalEmbedder:
    """BGE local embedding model (no API costs, works without any LLM API key)."""

    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5"):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    async def embed_query(self, text: str) -> List[float]:
        model = self._get_model()
        # BGE models benefit from instruction prefix for queries
        prefixed = f"Represent this sentence for searching relevant passages: {text}"
        embedding = model.encode(prefixed, normalize_embeddings=True)
        return embedding.tolist()

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
        return [e.tolist() for e in embeddings]

    @property
    def dimensions(self) -> int:
        dims = {
            "BAAI/bge-large-en-v1.5": 1024,
            "BAAI/bge-base-en-v1.5": 768,
            "BAAI/bge-small-en-v1.5": 384,
        }
        return dims.get(self.model_name, 1024)


_embedder_instance = None


def get_embedder() -> LocalEmbedder:
    """Return the local BGE embedder singleton.

    Groq does not provide an embeddings endpoint, so we always use the local
    sentence-transformer model (BAAI/bge-large-en-v1.5).
    """
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = LocalEmbedder()
    return _embedder_instance
