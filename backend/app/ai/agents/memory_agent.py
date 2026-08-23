from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.ai.agents.state import AgentState
from app.core.config import settings

HISTORY_WINDOW = 6  # last N messages to include as context


async def memory_agent(state: AgentState) -> AgentState:
    """Loads recent conversation history for context continuity."""
    if not state.get("session_id"):
        return {**state, "conversation_history": [], "agents_invoked": ["memory_agent"]}

    try:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            from app.models.chat import Message
            result = await db.execute(
                select(Message)
                .where(Message.session_id == state["session_id"])
                .order_by(Message.created_at.desc())
                .limit(HISTORY_WINDOW)
            )
            messages = result.scalars().all()

        await engine.dispose()

        # Format as LangChain-compatible history (oldest first)
        history = [
            {"role": m.role, "content": m.content}
            for m in reversed(messages)
        ]

    except Exception:
        history = []

    return {
        **state,
        "conversation_history": history,
        "agents_invoked": ["memory_agent"],
    }
