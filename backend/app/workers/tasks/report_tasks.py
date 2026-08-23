"""AI report generation worker."""
import asyncio
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2)
def generate_ai_report(self, report_id: str):
    try:
        asyncio.run(_generate_report_async(report_id))
    except Exception as exc:
        self.retry(exc=exc)


async def _generate_report_async(report_id: str):
    from sqlalchemy import select, func
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    from app.models.report import Report
    from app.models.document import Document
    from app.models.chat import ChatSession, Message
    from app.ai.llm import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    import datetime

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        result = await db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            return

        workspace_id = report.workspace_id
        since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)

        # Gather workspace stats
        doc_count = await db.scalar(
            select(func.count()).where(Document.workspace_id == workspace_id, Document.is_active == True)
        )
        chat_count = await db.scalar(
            select(func.count()).where(ChatSession.workspace_id == workspace_id, ChatSession.created_at >= since)
        )

        # Generate report with LLM
        llm = get_llm(temperature=0.3)
        messages = [
            SystemMessage(content="You are an AI assistant generating executive workspace analytics reports. Be professional, concise, and insight-driven."),
            HumanMessage(content=f"""Generate an executive summary report for the workspace.

Stats for last 30 days:
- Documents in knowledge base: {doc_count}
- Chat sessions: {chat_count}
- Report type: {report.report_type}

Create a professional markdown report with:
1. Executive Summary
2. Key Metrics
3. Notable Trends
4. Recommendations

Format as clean markdown.""")
        ]

        response = await llm.ainvoke(messages)
        report.content = response.content
        await db.commit()

    await engine.dispose()
