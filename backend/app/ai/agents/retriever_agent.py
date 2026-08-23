from app.ai.agents.state import AgentState
from app.ai.retrieval.hybrid_retriever import HybridRetriever


async def retriever_agent(state: AgentState) -> AgentState:
    """Performs hybrid semantic + keyword search across workspace documents."""
    query = state["query"]
    workspace_id = state["workspace_id"]
    intent = state.get("intent", "DOCUMENT_QA")

    # Build retrieval filters based on intent
    filters = {}
    if intent == "CODE_EXPLANATION":
        filters["file_type"] = ["code", "markdown"]
    elif intent == "RESEARCH_QUERY":
        filters["tags"] = ["research", "paper", "ai"]

    retriever = HybridRetriever()
    chunks = await retriever.search(
        query=query,
        workspace_id=workspace_id,
        filters=filters,
        top_k=8,
    )

    return {
        **state,
        "retrieved_chunks": chunks,
        "agents_invoked": ["retriever_agent"],
    }
