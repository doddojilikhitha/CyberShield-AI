import json
import logging
import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from models.schemas import IncidentReport, ApprovalMetadata, AuditLog
from db.database import get_db, get_incident, get_playbook, get_audit_logs
from reports.report_generator import ReportGenerator
from reports.pdf_export import export_report_to_pdf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{incident_id}", response_model=IncidentReport)
def get_report(incident_id: str, db: Session = Depends(get_db)):
    incident = get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    playbook = get_playbook(db, incident_id)
    audit_logs = get_audit_logs(db, incident_id=incident_id, limit=100)

    fc = {}
    if playbook:
        raw_fc = playbook.get("framework_context")
        if isinstance(raw_fc, dict):
            fc = raw_fc
        elif isinstance(raw_fc, str):
            try:
                fc = json.loads(raw_fc)
            except Exception:
                fc = {}

    approval_metadata = None
    if playbook and playbook.get("review_status") == "approved":
        approval_metadata = ApprovalMetadata(
            analyst_id=playbook.get("analyst_id"),
            approval_timestamp=playbook.get("approval_timestamp"),
            regeneration_attempts=playbook.get("regeneration_attempt_count", 0),
        )

    final_playbook = None
    if playbook:
        final_playbook = playbook.get("revised_playbook") or playbook.get(
            "generated_playbook"
        )

    return IncidentReport(
        incident_id=incident_id,
        incident_summary=incident["incident_description"],
        analyst_name=incident.get("analyst_name"),
        classification=playbook.get("incident_type") if playbook else None,
        severity=playbook.get("severity") if playbook else None,
        nist_mapping=fc.get("nist_phases", []),
        mitre_mapping=fc.get("mitre_techniques", []),
        owasp_guidance=fc.get("owasp_categories", []),
        final_playbook=final_playbook,
        approval_metadata=approval_metadata,
        audit_summary=[AuditLog(**log) for log in audit_logs],
        created_at=incident.get("created_at"),
        approved_at=playbook.get("approval_timestamp") if playbook else None,
    )


@router.get("/{incident_id}/pdf")
def download_pdf_report(incident_id: str, db: Session = Depends(get_db)):
    try:
        # Compile report payload first
        report_data = ReportGenerator.compile_report(db, incident_id)

        # Temp file path inside workspace
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        temp_dir = os.path.join(base_dir, "db", "temp_reports")
        os.makedirs(temp_dir, exist_ok=True)
        pdf_path = os.path.join(temp_dir, f"report_{incident_id}.pdf")

        # Generate the PDF
        export_report_to_pdf(report_data, pdf_path)

        return FileResponse(
            path=pdf_path,
            filename=f"CyberShield_Report_{incident_id[:8]}.pdf",
            media_type="application/pdf",
        )
    except Exception as e:
        logger.error(f"Failed to generate PDF for download: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
