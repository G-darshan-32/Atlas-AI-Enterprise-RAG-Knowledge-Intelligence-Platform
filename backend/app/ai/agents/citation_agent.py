import re
from app.ai.agents.state import AgentState


def extract_source_refs(text: str) -> list[int]:
    """Extract [Source N] references from response text."""
    matches = re.findall(r"\[Source\s+(\d+)\]", text)
    return list({int(m) for m in matches})


async def citation_agent(state: AgentState) -> AgentState:
    """Maps [Source N] references in response to actual document chunks."""
    draft = state.get("draft_response", "")
    chunks = state.get("retrieved_chunks", [])

    if not chunks:
        return {**state, "citations": [], "final_response": draft, "agents_invoked": ["citation_agent"]}

    referenced_indices = extract_source_refs(draft)

    citations = []
    for idx in referenced_indices:
        chunk_idx = idx - 1  # 0-based
        if 0 <= chunk_idx < len(chunks):
            chunk = chunks[chunk_idx]
            citations.append({
                "source_number": idx,
                "document_id": chunk.get("document_id"),
                "title": chunk.get("title", "Unknown"),
                "chunk_index": chunk.get("chunk_index"),
                "page_number": chunk.get("page_number"),
                "score": chunk.get("score", 0.0),
                "content_preview": chunk.get("content", "")[:200],
            })

    # Calculate confidence from retrieval scores
    if chunks:
        top_scores = [c.get("score", 0.0) for c in chunks[:3]]
        avg_score = sum(top_scores) / len(top_scores) if top_scores else 0.0
        # Normalize Qdrant cosine similarity (0-1) to confidence
        confidence = min(0.99, max(0.1, avg_score))
    else:
        confidence = 0.3

    return {
        **state,
        "citations": citations,
        "final_response": draft,
        "confidence_score": confidence,
        "agents_invoked": ["citation_agent"],
    }
