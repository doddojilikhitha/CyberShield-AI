import json
import logging
import time

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from models.schemas import (
    GeneratePlaybookRequest,
    ApprovePlaybookRequest,
    RejectPlaybookRequest,
    RegeneratePlaybookRequest,
    PlaybookResponse,
    FrameworkContext,
)
from db.database import (
    get_db,
    get_incident,
    get_playbook,
    create_or_update_playbook,
    update_incident_status,
    create_audit_log,
    now_iso,
)
from security.prompt_guard import PromptGuard
from security.validators import SecurityValidator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/playbooks", tags=["playbooks"])


def _playbook_row_to_response(row: dict) -> PlaybookResponse:
    fc = row.get("framework_context")
    framework_context = None
    if fc:
        if isinstance(fc, dict):
            framework_context = FrameworkContext(**fc)
        elif isinstance(fc, str):
            try:
                framework_context = FrameworkContext(**json.loads(fc))
            except Exception:
                pass
    return PlaybookResponse(
        incident_id=row["incident_id"],
        incident_type=row.get("incident_type"),
        severity=row.get("severity"),
        framework_context=framework_context,
        generated_playbook=row.get("generated_playbook"),
        revised_playbook=row.get("revised_playbook"),
        review_status=row.get("review_status", "pending_review"),
        reviewer_feedback=row.get("reviewer_feedback"),
        processing_time=row.get("processing_time"),
        generation_duration_ms=row.get("generation_duration_ms"),
        regeneration_attempt_count=row.get("regeneration_attempt_count", 0),
        approval_timestamp=row.get("approval_timestamp"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.post("/generate", response_model=PlaybookResponse)
def generate_playbook(body: GeneratePlaybookRequest, db: Session = Depends(get_db)):
    incident = get_incident(db, body.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    create_or_update_playbook(db, body.incident_id, {"review_status": "generating"})
    update_incident_status(db, body.incident_id, "processing")

    start = time.time()
    try:
        from graph.workflow import run_generation_workflow

        result = run_generation_workflow(incident, db)

        framework_context = result.get("framework_context") or {}
        duration_ms = result.get("generation_duration_ms") or int(
            (time.time() - start) * 1000
        )

        create_or_update_playbook(
            db,
            body.incident_id,
            {
                "incident_type": result.get("incident_type"),
                "severity": result.get("severity"),
                "framework_context": json.dumps(framework_context),
                "generated_playbook": result.get("generated_playbook"),
                "review_status": "pending_review",
                "processing_time": time.time() - start,
                "generation_duration_ms": duration_ms,
                "regeneration_attempt_count": result.get(
                    "regeneration_attempt_count", 0
                ),
            },
        )
        update_incident_status(db, body.incident_id, "pending_review")

        row = get_playbook(db, body.incident_id)
        assert row is not None
        return _playbook_row_to_response(row)

    except Exception as e:
        logger.error(f"Generation error for {body.incident_id}: {e}")
        create_or_update_playbook(
            db,
            body.incident_id,
            {
                "review_status": "error",
                "generated_playbook": f"Generation failed: {str(e)}",
            },
        )
        update_incident_status(db, body.incident_id, "error")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/approve", response_model=PlaybookResponse)
def approve_playbook(body: ApprovePlaybookRequest, db: Session = Depends(get_db)):
    body.analyst_id = SecurityValidator.sanitize_string(body.analyst_id)
    row = get_playbook(db, body.incident_id)
    if not row:
        raise HTTPException(status_code=404, detail="Playbook not found")

    approval_ts = now_iso()
    create_or_update_playbook(
        db,
        body.incident_id,
        {
            "review_status": "approved",
            "analyst_id": body.analyst_id,
            "approval_timestamp": approval_ts,
        },
    )
    update_incident_status(db, body.incident_id, "approved")

    create_audit_log(
        db,
        {
            "incident_id": body.incident_id,
            "agent_name": "human_review",
            "model_used": None,
            "input_summary": f"Analyst {body.analyst_id} approved playbook",
            "output_summary": "Playbook approved",
            "processing_time_ms": 0,
            "approval_status": "approved",
        },
    )

    row = get_playbook(db, body.incident_id)
    assert row is not None
    return _playbook_row_to_response(row)


@router.post("/reject", response_model=PlaybookResponse)
def reject_playbook(body: RejectPlaybookRequest, db: Session = Depends(get_db)):
    body.analyst_id = SecurityValidator.sanitize_string(body.analyst_id)
    body.feedback = SecurityValidator.validate_payload(body.feedback)
    PromptGuard.validate_input(body.feedback)

    row = get_playbook(db, body.incident_id)
    if not row:
        raise HTTPException(status_code=404, detail="Playbook not found")

    create_or_update_playbook(
        db,
        body.incident_id,
        {
            "review_status": "rejected",
            "reviewer_feedback": body.feedback,
            "analyst_id": body.analyst_id,
        },
    )
    update_incident_status(db, body.incident_id, "rejected")

    create_audit_log(
        db,
        {
            "incident_id": body.incident_id,
            "agent_name": "human_review",
            "model_used": None,
            "input_summary": f"Analyst {body.analyst_id} rejected with feedback: {body.feedback[:100]}",
            "output_summary": "Playbook rejected",
            "processing_time_ms": 0,
            "approval_status": "rejected",
        },
    )

    row = get_playbook(db, body.incident_id)
    assert row is not None
    return _playbook_row_to_response(row)


@router.post("/regenerate", response_model=PlaybookResponse)
def regenerate_playbook(body: RegeneratePlaybookRequest, db: Session = Depends(get_db)):
    incident = get_incident(db, body.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    row = get_playbook(db, body.incident_id)
    if not row:
        raise HTTPException(status_code=404, detail="Playbook not found")

    create_or_update_playbook(db, body.incident_id, {"review_status": "generating"})
    update_incident_status(db, body.incident_id, "processing")

    try:
        from graph.workflow import run_generation_workflow

        fc = row.get("framework_context")
        if isinstance(fc, str):
            try:
                fc = json.loads(fc)
            except Exception:
                fc = {}

        incident_data = {
            **incident,
            "framework_context": fc,
            "generated_playbook": row.get("generated_playbook"),
            "reviewer_feedback": row.get("reviewer_feedback"),
            "regeneration_attempt_count": row.get("regeneration_attempt_count", 0),
        }
        result = run_generation_workflow(incident_data, db)

        framework_context = result.get("framework_context") or fc or {}
        duration_ms = result.get("generation_duration_ms", 0)

        create_or_update_playbook(
            db,
            body.incident_id,
            {
                "incident_type": result.get("incident_type")
                or row.get("incident_type"),
                "severity": result.get("severity") or row.get("severity"),
                "framework_context": json.dumps(framework_context),
                "generated_playbook": result.get("generated_playbook"),
                "revised_playbook": result.get("revised_playbook"),
                "review_status": "pending_review",
                "reviewer_feedback": None,
                "generation_duration_ms": duration_ms,
                "regeneration_attempt_count": result.get(
                    "regeneration_attempt_count", 0
                ),
            },
        )
        update_incident_status(db, body.incident_id, "pending_review")

        row = get_playbook(db, body.incident_id)
        assert row is not None
        return _playbook_row_to_response(row)

    except Exception as e:
        logger.error(f"Regeneration error for {body.incident_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")


@router.get("/{incident_id}", response_model=PlaybookResponse)
def get_playbook_route(incident_id: str, db: Session = Depends(get_db)):
    row = get_playbook(db, incident_id)
    if not row:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return _playbook_row_to_response(row)
