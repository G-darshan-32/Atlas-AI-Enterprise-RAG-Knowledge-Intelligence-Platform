"""Research Agent — specialised retrieval for academic papers and AI research."""
from app.ai.agents.state import AgentState
from app.ai.retrieval.hybrid_retriever import HybridRetriever


async def research_agent(state: AgentState) -> AgentState:
    """
    Retrieves from research-tagged content: papers, blogs, technical reports.
    Prioritises high-quality embeddings from semantic-dense academic text.
    """
    retriever = HybridRetriever()
    chunks = await retriever.search(
        query=state["query"],
        workspace_id=state["workspace_id"],
        filters={"tags": ["research", "paper", "ai", "ml"]},
        top_k=8,
    )

    # If tag filter returned nothing, fall back to unfiltered search
    if not chunks:
        chunks = await retriever.search(
            query=state["query"],
            workspace_id=state["workspace_id"],
            top_k=8,
        )

    return {
        **state,
        "retrieved_chunks": chunks,
        "agents_invoked": ["research_agent"],
    }
