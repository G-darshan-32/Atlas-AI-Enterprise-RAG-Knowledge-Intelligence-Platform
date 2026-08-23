"""Report Agent — generates executive summaries and structured reports."""
from langchain_core.messages import SystemMessage, HumanMessage
from app.ai.agents.state import AgentState
from app.ai.agents.citation_agent import citation_agent
from app.ai.llm import get_llm


REPORT_SYSTEM = """You are an executive report writer for an enterprise AI platform.
Given retrieved context from the organization's knowledge base, generate a
well-structured, professional report in markdown format.

Structure your reports with:
- Executive Summary (2-3 sentences)
- Key Findings (bullet points)
- Detailed Analysis (prose)
- Recommendations (actionable items)
- Sources (cite [Source N] references)

Be concise, professional, and insight-driven."""


async def report_agent(state: AgentState) -> AgentState:
    """
    Generates a structured executive report from retrieved context.
    Used when intent is REPORT_REQUEST or SUMMARIZATION.
    """
    chunks = state.get("retrieved_chunks", [])

    context_parts = []
    for i, chunk in enumerate(chunks[:6], 1):
        context_parts.append(f"[Source {i}] {chunk.get('title', 'Document')}:\n{chunk.get('content', '')}")
    context = "\n\n---\n\n".join(context_parts) if context_parts else "No specific documents retrieved."

    llm = get_llm(temperature=0.3)

    response = await llm.ainvoke([
        SystemMessage(content=REPORT_SYSTEM),
        HumanMessage(content=f"Context:\n{context}\n\nGenerate a report for: {state['query']}"),
    ])

    updated_state = {
        **state,
        "draft_response": response.content,
        "agents_invoked": ["report_agent"],
    }

    # Pass through citation agent to attach source references
    return await citation_agent(updated_state)
