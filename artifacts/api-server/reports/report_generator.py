import json
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from db.database import (
    get_incident,
    get_playbook,
    get_audit_logs,
    create_or_update_report,
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    @staticmethod
    def compile_report(db: Session, incident_id: str) -> Dict[str, Any]:
        """
        Retrieves database entries for an incident and compiles them
        into a structured report payload.
        """
        incident = get_incident(db, incident_id)
        if not incident:
            raise ValueError(f"Incident with ID {incident_id} not found.")

        playbook = get_playbook(db, incident_id) or {}
        audit_logs = get_audit_logs(db, incident_id=incident_id, limit=100)

        # Parse framework context
        fc = {}
        raw_fc = playbook.get("framework_context")
        if raw_fc:
            if isinstance(raw_fc, dict):
                fc = raw_fc
            elif isinstance(raw_fc, str):
                try:
                    fc = json.loads(raw_fc)
                except Exception:
                    fc = {}

        # Construct approval metadata
        approval_metadata = None
        if playbook.get("review_status") == "approved":
            approval_metadata = {
                "analyst_id": playbook.get("analyst_id"),
                "approval_timestamp": playbook.get("approval_timestamp"),
                "regeneration_attempts": playbook.get("regeneration_attempt_count", 0),
            }

        final_playbook = playbook.get("revised_playbook") or playbook.get(
            "generated_playbook"
        )

        report_payload = {
            "incident_id": incident_id,
            "incident_summary": incident.get("incident_description", ""),
            "analyst_name": incident.get("analyst_name"),
            "classification": playbook.get("incident_type"),
            "severity": playbook.get("severity"),
            "nist_mapping": fc.get("nist_phases", []),
            "mitre_mapping": fc.get("mitre_techniques", []),
            "owasp_guidance": fc.get("owasp_categories", []),
            "final_playbook": final_playbook,
            "approval_metadata": approval_metadata,
            "audit_summary": [
                {
                    "id": log.get("id"),
                    "agent_name": log.get("agent_name"),
                    "timestamp": log.get("timestamp"),
                    "model_used": log.get("model_used"),
                    "input_summary": log.get("input_summary"),
                    "output_summary": log.get("output_summary"),
                    "processing_time_ms": log.get("processing_time_ms"),
                    "approval_status": log.get("approval_status"),
                }
                for log in audit_logs
            ],
            "created_at": incident.get("created_at"),
            "approved_at": playbook.get("approval_timestamp"),
        }

        # Store in database
        create_or_update_report(db, incident_id, report_payload)
        logger.info(
            f"Incident report generated and cached in DB for incident: {incident_id}"
        )

        return report_payload
