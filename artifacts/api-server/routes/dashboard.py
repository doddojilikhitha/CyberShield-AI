import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.schemas import DashboardMetrics, AgentStats, RecentIncidentItem
from db.database import get_db, get_dashboard_metrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
def get_metrics(db: Session = Depends(get_db)):
    data = get_dashboard_metrics(db)
    return DashboardMetrics(
        total_incidents=data["total_incidents"],
        approved_playbooks=data["approved_playbooks"],
        rejected_playbooks=data["rejected_playbooks"],
        pending_review=data["pending_review"],
        avg_generation_time_ms=data["avg_generation_time_ms"],
        recent_incidents=[RecentIncidentItem(**r) for r in data["recent_incidents"]],
        agent_stats=AgentStats(**data["agent_stats"]),
    )
