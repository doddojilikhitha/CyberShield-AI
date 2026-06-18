import json
import logging
import time
import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)
PROMPT_DIR = Path(__file__).parent.parent / "prompts"


def run_compliance_reviewer(state: dict, db_session=None, callbacks=None) -> dict:
    start_time = time.time()
    incident_id = state.get("incident_id", "unknown")
    incident_type = state.get("incident_type", "unknown")
    severity = state.get("severity", "medium")
    generated_playbook = state.get("generated_playbook", "")
    framework_context = state.get("framework_context", {})

    try:
        nist_phases = framework_context.get("nist_phases", [])
        mitre_techniques = framework_context.get("mitre_techniques", [])
        owasp_categories = framework_context.get("owasp_categories", [])

        prompt_template = (PROMPT_DIR / "reviewer.txt").read_text()
        prompt = prompt_template.format(
            incident_type=incident_type,
            severity=severity,
            nist_phases=", ".join(nist_phases) if nist_phases else "None mapped",
            mitre_techniques=(
                ", ".join(mitre_techniques[:5]) if mitre_techniques else "None mapped"
            ),
            owasp_categories=(
                ", ".join(owasp_categories) if owasp_categories else "None applicable"
            ),
            generated_playbook=generated_playbook[:4000],
        )

        llm = ChatOpenAI(
            model=os.getenv("FAST_LLM_MODEL", "gpt-4o-mini"),
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),  # type: ignore[call-arg]
            callbacks=callbacks or [],
        )
        response = llm.invoke(
            [
                SystemMessage(
                    content="You are a cybersecurity compliance reviewer. Always respond with valid JSON."
                ),
                HumanMessage(content=prompt),
            ]
        )

        if not isinstance(response.content, str):
            raise ValueError("Expected string response from LLM")
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        review = json.loads(content)
        duration_ms = int((time.time() - start_time) * 1000)
        compliance_notes = f"Score: {review.get('compliance_score', 0)}/100. Gaps: {', '.join(review.get('gaps', [])[:3])}"

        if db_session:
            from db.database import create_audit_log

            create_audit_log(
                db_session,
                {
                    "incident_id": incident_id,
                    "agent_name": "compliance_reviewer",
                    "model_used": "gpt-4o-mini",
                    "input_summary": f"Reviewing playbook for {incident_type}",
                    "output_summary": compliance_notes,
                    "processing_time_ms": duration_ms,
                    "approval_status": "completed",
                },
            )

        return {
            **state,
            "compliance_notes": compliance_notes,
            "compliance_review": review,
            "review_status": "pending_review",
            "audit_events": state.get("audit_events", [])
            + [
                {
                    "agent": "compliance_reviewer",
                    "duration_ms": duration_ms,
                    "result": compliance_notes,
                }
            ],
        }
    except Exception as e:
        logger.error(f"Compliance reviewer error: {e}")
        return {
            **state,
            "compliance_notes": f"Review error: {str(e)}",
            "review_status": "pending_review",
            "error": str(e),
        }
