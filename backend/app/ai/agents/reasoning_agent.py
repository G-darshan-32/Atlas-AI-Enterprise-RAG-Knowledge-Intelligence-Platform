from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.ai.agents.state import AgentState
from app.core.config import settings
import tiktoken

SYSTEM_PROMPT = """You are Atlas AI, an expert enterprise knowledge assistant.
Your job is to answer questions using the provided context from the organization's knowledge base.

Guidelines:
- Answer based on the provided context. If the context doesn't contain enough information, say so clearly.
- Be precise and cite sources using [Source N] notation where N corresponds to the numbered sources.
- Format code blocks properly using markdown.
- For technical questions, be specific and detailed.
- If comparing multiple sources, structure your answer clearly.
- Never fabricate information not present in the context.
- Confidence should reflect how well the context supports your answer.

Context:
{context}

Conversation History is included in the messages."""

HUMAN_TEMPLATE = """Question: {query}

Please answer based on the provided context. Include [Source N] citations."""


def build_context_string(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant documents found in the knowledge base."

    parts = []
    for i, chunk in enumerate(chunks, 1):
        title = chunk.get("title", "Unknown Document")
        page = chunk.get("page_number")
        page_str = f", page {page}" if page else ""
        parts.append(f"[Source {i}] {title}{page_str}:\n{chunk.get('content', '')}")

    return "\n\n---\n\n".join(parts)


def estimate_tokens(text: str) -> int:
    try:
        enc = tiktoken.get_encoding("cl100k_base")  # provider-agnostic token estimator
        return len(enc.encode(text))
    except Exception:
        return len(text) // 4


async def reasoning_agent(state: AgentState) -> AgentState:
    """Generates the final response using context and conversation history."""
    chunks = state.get("retrieved_chunks", [])
    history = state.get("conversation_history", [])
    query = state["query"]

    context = build_context_string(chunks)

    from app.ai.llm import get_llm
    llm = get_llm(temperature=0.2, streaming=False)

    # Build message list
    messages = [SystemMessage(content=SYSTEM_PROMPT.format(context=context))]

    # Add conversation history
    for msg in history[-4:]:  # last 4 messages for context
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    # Add current query
    messages.append(HumanMessage(content=HUMAN_TEMPLATE.format(query=query)))

    response = await llm.ainvoke(messages)
    draft = response.content

    # Estimate token usage
    total_tokens = estimate_tokens(context) + estimate_tokens(query) + estimate_tokens(draft)

    return {
        **state,
        "draft_response": draft,
        "tokens_used": total_tokens,
        "agents_invoked": ["reasoning_agent"],
    }
