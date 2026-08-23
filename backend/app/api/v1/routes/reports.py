from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import datetime

from app.core.database import get_db
from app.models import User, Report, WorkspaceMember
from app.api.dependencies import get_current_user, get_workspace_member, require_role

router = APIRouter()


@router.get("/{workspace_id}/reports")
async def list_reports(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(Report).where(Report.workspace_id == workspace_id).order_by(Report.created_at.desc())
    )
    reports = result.scalars().all()
    return [{"id": str(r.id), "title": r.title, "report_type": r.report_type, "created_at": r.created_at.isoformat()} for r in reports]


@router.post("/{workspace_id}/reports/generate")
async def generate_report(
    workspace_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "manager", "super_admin")),
):
    report_type = body.get("type", "workspace_summary")
    title = body.get("title", f"{report_type.replace('_', ' ').title()} — {datetime.datetime.now().strftime('%B %Y')}")

    report = Report(
        workspace_id=workspace_id,
        generated_by=current_user.id,
        report_type=report_type,
        title=title,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # Queue AI report generation
    from app.workers.tasks.report_tasks import generate_ai_report
    generate_ai_report.delay(str(report.id))

    return {"id": str(report.id), "title": report.title, "status": "generating"}
