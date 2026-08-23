"""Unified LLM factory helper — uses Groq as the sole LLM provider."""
from typing import Optional
from langchain_groq import ChatGroq
from app.core.config import settings


def get_llm(model: Optional[str] = None, temperature: float = 0.2, streaming: bool = False) -> ChatGroq:
    """Instantiate a ChatGroq model using the GROQ_API_KEY from settings."""
    return ChatGroq(
        model=model or settings.GROQ_MODEL,
        temperature=temperature,
        api_key=settings.GROQ_API_KEY,
        streaming=streaming,
    )
