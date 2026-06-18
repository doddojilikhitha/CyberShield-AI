import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from models.schemas import AuditLog
from db.database import get_db, get_audit_logs, get_traces

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=list[AuditLog])
def list_audit_logs(
    incidentId: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    logs = get_audit_logs(db, incident_id=incidentId, limit=limit)
    return logs


@router.get("/traces")
def list_traces(
    incidentId: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Self-hosted LangSmith alternative — full LLM call traces for every
    agent run, stored locally in SQLite. No external account needed.
    Returns: event_type, agent_name, model_used, input/output summaries,
             processing_time_ms, token usage metadata, timestamp.
    """
    traces = get_traces(db, incident_id=incidentId, limit=limit)
    return traces
