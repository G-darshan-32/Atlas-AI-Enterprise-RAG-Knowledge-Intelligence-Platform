from app.ai.agents.state import AgentState
from app.ai.retrieval.hybrid_retriever import HybridRetriever


async def github_agent(state: AgentState) -> AgentState:
    """Specialized retrieval for GitHub repository content (code, docs, READMEs)."""
    query = state["query"]
    workspace_id = state["workspace_id"]

    retriever = HybridRetriever()

    # Search specifically in GitHub-indexed content
    chunks = await retriever.search(
        query=query,
        workspace_id=workspace_id,
        filters={"source_type": "github"},
        top_k=6,
    )

    return {
        **state,
        "retrieved_chunks": chunks,
        "agents_invoked": ["github_agent"],
    }
