import logging
import time
import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)
PROMPT_DIR = Path(__file__).parent.parent / "prompts"


def run_playbook_generator(state: dict, db_session=None, callbacks=None) -> dict:
    start_time = time.time()
    incident_id = state.get("incident_id", "unknown")
    incident_type = state.get("incident_type", "unknown")
    severity = state.get("severity", "medium")
    incident_description = state.get("incident_description", "")
    framework_context = state.get("framework_context", {})
    retrieved_context = state.get("retrieved_context", "")

    try:
        nist_phases = framework_context.get("nist_phases", [])
        mitre_techniques = framework_context.get("mitre_techniques", [])
        owasp_categories = framework_context.get("owasp_categories", [])

        prompt_template = (PROMPT_DIR / "generator.txt").read_text()
        prompt = prompt_template.format(
            incident_id=incident_id,
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
            retrieved_context=(
                retrieved_context[:3000]
                if retrieved_context
                else "No additional context available."
            ),
        )

        llm = ChatOpenAI(
            model=os.getenv("SLOW_LLM_MODEL", "gpt-4o"),
            temperature=0.1,
            max_tokens=4000,  # type: ignore[call-arg]
            openai_api_key=os.getenv("OPENAI_API_KEY"),  # type: ignore[call-arg]
            callbacks=callbacks or [],
        )
        response = llm.invoke(
            [
                SystemMessage(
                    content="You are an expert cybersecurity incident response specialist. Generate comprehensive, actionable playbooks in Markdown format."
                ),
                HumanMessage(content=prompt),
            ]
        )

        if not isinstance(response.content, str):
            raise ValueError("Expected string response from LLM")
        playbook = response.content.strip()
        duration_ms = int((time.time() - start_time) * 1000)

        if db_session:
            from db.database import create_audit_log

            create_audit_log(
                db_session,
                {
                    "incident_id": incident_id,
                    "agent_name": "playbook_generator",
                    "model_used": "gpt-4o",
                    "input_summary": f"Type: {incident_type}, Severity: {severity}",
                    "output_summary": f"Generated playbook ({len(playbook)} chars)",
                    "processing_time_ms": duration_ms,
                    "approval_status": "completed",
                },
            )

        return {
            **state,
            "generated_playbook": playbook,
            "generation_duration_ms": duration_ms,
            "audit_events": state.get("audit_events", [])
            + [
                {
                    "agent": "playbook_generator",
                    "duration_ms": duration_ms,
                    "result": f"Generated {len(playbook)} char playbook",
                }
            ],
        }
    except Exception as e:
        logger.error(f"Playbook generator error: {e}")
        return {
            **state,
            "generated_playbook": f"# Incident Response Playbook\n\n**Error during generation**: {str(e)}\n\nPlease retry or contact the security team.",
            "error": str(e),
        }
