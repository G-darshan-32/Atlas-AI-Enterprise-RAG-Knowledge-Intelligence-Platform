"""Prompt injection detection and input sanitisation."""
import re
from fastapi import HTTPException, status

# Patterns commonly used in prompt injection attacks
_INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above|prior)\s+instructions",
    r"disregard\s+(your|all|previous)\s+(instructions|context|rules)",
    r"you\s+are\s+now\s+(a|an|the)\s+\w+",
    r"act\s+as\s+(a|an|the)\s+(different|new|unrestricted)",
    r"new\s+instructions?\s*:",
    r"system\s*prompt\s*:",
    r"<\s*system\s*>",
    r"\[INST\]",
    r"###\s*instruction",
    r"jailbreak",
    r"DAN\s+mode",
    r"do\s+anything\s+now",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]

MAX_QUERY_LENGTH = 4000


def sanitise_query(query: str) -> str:
    """
    Validate and sanitise a user query before passing to the AI pipeline.
    Raises HTTP 422 on suspected prompt injection.
    Returns the cleaned query on success.
    """
    if not query or not query.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Query cannot be empty")

    if len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters",
        )

    for pattern in _COMPILED:
        if pattern.search(query):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Query contains disallowed content",
            )

    # Strip null bytes and control characters (except newlines/tabs)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", query)
    return cleaned.strip()
