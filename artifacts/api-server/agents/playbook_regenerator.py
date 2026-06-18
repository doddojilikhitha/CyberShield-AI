import logging
import time
import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)
PROMPT_DIR = Path(__file__).parent.parent / "prompts"


def run_playbook_regenerator(state: dict, db_session=None, callbacks=None) -> dict:
    start_time = time.time()
    incident_id = state.get("incident_id", "unknown")
    incident_type = state.get("incident_type", "unknown")
    severity = state.get("severity", "medium")
    incident_description = state.get("incident_description", "")
    framework_context = state.get("framework_context", {})
    retrieved_context = state.get("retrieved_context", "")
    original_playbook = state.get("generated_playbook", "")
    reviewer_feedback = state.get("reviewer_feedback", "")
    compliance_notes = state.get("compliance_notes", "")
    attempt = state.get("regeneration_attempt_count", 0) + 1

    try:
        nist_phases = framework_context.get("nist_phases", [])
        mitre_techniques = framework_context.get("mitre_techniques", [])
        owasp_categories = framework_context.get("owasp_categories", [])

        prompt_template = (PROMPT_DIR / "regenerator.txt").read_text()
        prompt = prompt_template.format(
            incident_type=incident_type,
            severity=severity,
            incident_description=incident_description,
            nist_phases=", ".join(nist_phases) if nist_phases else "All phases",
            mitre_techniques=(
                "\n".join([f"- {t}" for t in mitre_techniques])
                if mitre_techniques
                else "- Not mapped"
            ),
            owasp_categories=(
                "\n".join([f"- {c}" for c in owasp_categories])
                if owasp_categories
                else "- Not applicable"
            ),
            original_playbook=original_playbook[:3000],
            reviewer_feedback=reviewer_feedback or "No specific feedback provided.",
            compliance_notes=compliance_notes or "No compliance notes.",
            retrieved_context=(
                retrieved_context[:2000]
                if retrieved_context
                else "No additional context."
            ),
            regeneration_attempt=attempt,
        )

        llm = ChatOpenAI(
            model=os.getenv("SLOW_LLM_MODEL", "gpt-4o"),
            temperature=0.2,
            max_tokens=4000,  # type: ignore[call-arg]
            openai_api_key=os.getenv("OPENAI_API_KEY"),  # type: ignore[call-arg]
            callbacks=callbacks or [],
        )
        response = llm.invoke(
            [
                SystemMessage(
                    content="You are an expert cybersecurity incident response specialist. Generate significantly improved playbooks based on analyst feedback."
                ),
                HumanMessage(content=prompt),
            ]
        )

        if not isinstance(response.content, str):
            raise ValueError("Expected string response from LLM")
        revised_playbook = response.content.strip()
        duration_ms = int((time.time() - start_time) * 1000)

        if db_session:
            from db.database import create_audit_log

            create_audit_log(
                db_session,
                {
                    "incident_id": incident_id,
                    "agent_name": "playbook_regenerator",
                    "model_used": "gpt-4o",
                    "input_summary": f"Attempt #{attempt}, Feedback: {reviewer_feedback[:100]}",
                    "output_summary": f"Regenerated playbook ({len(revised_playbook)} chars)",
                    "processing_time_ms": duration_ms,
                    "approval_status": "completed",
                },
            )

        return {
            **state,
            "revised_playbook": revised_playbook,
            "generated_playbook": revised_playbook,
            "regeneration_attempt_count": attempt,
            "review_status": "pending_review",
            "reviewer_feedback": None,
            "audit_events": state.get("audit_events", [])
            + [
                {
                    "agent": "playbook_regenerator",
                    "duration_ms": duration_ms,
                    "result": f"Regenerated (attempt #{attempt})",
                }
            ],
        }
    except Exception as e:
        logger.error(f"Playbook regenerator error: {e}")
        return {
            **state,
            "regeneration_attempt_count": attempt,
            "review_status": "pending_review",
            "error": str(e),
        }
