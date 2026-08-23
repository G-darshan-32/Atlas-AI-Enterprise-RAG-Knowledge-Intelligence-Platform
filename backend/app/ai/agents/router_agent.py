from langchain_core.prompts import ChatPromptTemplate
from app.ai.agents.state import AgentState
from app.core.config import settings

INTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a query router for an enterprise AI knowledge platform.
Classify the user query into exactly one intent category.

Categories:
- DOCUMENT_QA: Questions about policies, HR docs, handbooks, procedures, meeting notes
- CODE_EXPLANATION: Questions about code, repositories, APIs, architecture, technical implementation
- RESEARCH_QUERY: Questions about research papers, AI models, scientific topics
- GENERAL_CHAT: Greetings, general conversation, meta questions about the assistant
- COMPARISON: Comparing multiple documents, systems, or approaches
- SUMMARIZATION: Requests to summarize a document or topic
- REPORT_REQUEST: Requests for reports, executive summaries
- ANALYTICS: Questions about workspace usage metrics, active users, query trends, storage stats

Respond with ONLY the category name and a 0-1 confidence score, comma-separated.
Example: DOCUMENT_QA,0.95"""),
    ("human", "Query: {query}\nMode: {mode}"),
])


async def router_agent(state: AgentState) -> AgentState:
    """Classifies user intent to route to correct downstream agents."""
    from app.ai.llm import get_llm
    llm = get_llm(temperature=0)
    chain = INTENT_PROMPT | llm

    try:
        response = await chain.ainvoke({"query": state["query"], "mode": state["mode"]})
        parts = response.content.strip().split(",")
        intent = parts[0].strip()
        confidence = float(parts[1].strip()) if len(parts) > 1 else 0.7

        # Validate intent
        valid_intents = {
            "DOCUMENT_QA", "CODE_EXPLANATION", "RESEARCH_QUERY", "GENERAL_CHAT",
            "COMPARISON", "SUMMARIZATION", "REPORT_REQUEST", "ANALYTICS"
        }
        if intent not in valid_intents:
            intent = "DOCUMENT_QA"

    except Exception:
        # Fallback: keyword heuristics
        query_lower = state["query"].lower()
        if any(kw in query_lower for kw in ["code", "function", "api", "repository", "github", "class", "method", "bug", "error"]):
            intent = "CODE_EXPLANATION"
        elif any(kw in query_lower for kw in ["paper", "research", "model", "transformer", "bert", "llm"]):
            intent = "RESEARCH_QUERY"
        elif any(kw in query_lower for kw in ["summarize", "summary", "tldr", "brief"]):
            intent = "SUMMARIZATION"
        elif any(kw in query_lower for kw in ["compare", "difference", "vs ", "versus"]):
            intent = "COMPARISON"
        elif any(kw in query_lower for kw in ["analytics", "metrics", "usage stats", "active users", "token usage"]):
            intent = "ANALYTICS"
        elif any(kw in query_lower for kw in ["report", "executive summary", "generate report"]):
            intent = "REPORT_REQUEST"
        else:
            intent = "DOCUMENT_QA"
        confidence = 0.6

    return {
        **state,
        "intent": intent,
        "confidence_score": confidence,
        "agents_invoked": ["router_agent"],
    }
