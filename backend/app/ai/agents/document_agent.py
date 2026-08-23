"""Document Agent — handles questions about uploaded documents (policies, handbooks, specs)."""
from app.ai.agents.state import AgentState
from app.ai.retrieval.hybrid_retriever import HybridRetriever


async def document_agent(state: AgentState) -> AgentState:
    """
    Targeted retrieval for document Q&A.
    If the session has scoped document_ids, search only within those.
    Otherwise search across all workspace documents.
    """
    # Check if chat session has scoped document context
    # (passed via state or session metadata — simplified here to workspace-wide)
    retriever = HybridRetriever()
    chunks = await retriever.search(
        query=state["query"],
        workspace_id=state["workspace_id"],
        filters={"source_type": "document"},
        top_k=8,
    )

    return {
        **state,
        "retrieved_chunks": chunks,
        "agents_invoked": ["document_agent"],
    }
