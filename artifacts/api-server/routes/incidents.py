import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from models.schemas import CreateIncidentRequest, IncidentResponse
from db.database import get_db, create_incident, get_incident, list_incidents
from security.prompt_guard import PromptGuard
from security.validators import SecurityValidator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("", response_model=IncidentResponse, status_code=201)
def create_incident_route(body: CreateIncidentRequest, db: Session = Depends(get_db)):
    try:
        # Sanitize and check input parameters
        body.incident_description = SecurityValidator.validate_payload(
            body.incident_description
        )
        PromptGuard.validate_input(body.incident_description)
        body.analyst_name = SecurityValidator.sanitize_string(body.analyst_name)
        if body.incident_source:
            body.incident_source = SecurityValidator.sanitize_string(
                body.incident_source
            )

        incident = create_incident(db, body.model_dump())
        return incident
    except Exception as e:
        logger.error(f"Create incident error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[IncidentResponse])
def list_incidents_route(db: Session = Depends(get_db)):
    return list_incidents(db)


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident_route(incident_id: str, db: Session = Depends(get_db)):
    incident = get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
