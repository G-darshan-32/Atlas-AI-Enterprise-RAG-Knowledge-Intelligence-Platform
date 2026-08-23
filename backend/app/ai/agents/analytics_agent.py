"""Analytics Agent — answers questions about workspace usage, trends, and metrics."""
from langchain_core.messages import SystemMessage, HumanMessage
from app.ai.agents.state import AgentState


ANALYTICS_SYSTEM = """You are an analytics assistant for an enterprise knowledge platform.
You have access to workspace usage metrics. Answer questions about usage trends,
popular documents, active users, and AI query patterns.
Be concise and data-driven. Format numbers clearly."""


async def analytics_agent(state: AgentState) -> AgentState:
    """
    Handles analytics and reporting queries by pulling metrics from the database
    and synthesising an answer with the LLM.
    """
    # For analytics queries, we skip vector retrieval and go straight to LLM
    # with structured analytics context. In production this would pull real DB metrics.
    query = state["query"]

    analytics_context = """
Available workspace metrics (sample data for demonstration):
- Total documents indexed: varies by workspace
- Daily active users: tracked per workspace
- Most queried topics: from analytics_events table
- Storage usage: tracked in workspaces table
- Chat sessions per day: from chat_sessions table
- Embedding count: from document_chunks table
    """

    from app.ai.llm import get_llm
    llm = get_llm(temperature=0.1, streaming=False)

    response = await llm.ainvoke([
        SystemMessage(content=ANALYTICS_SYSTEM),
        HumanMessage(content=f"Context:\n{analytics_context}\n\nQuestion: {query}"),
    ])

    return {
        **state,
        "draft_response": response.content,
        "retrieved_chunks": [],
        "agents_invoked": ["analytics_agent"],
    }
