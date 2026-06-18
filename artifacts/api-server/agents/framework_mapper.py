import json
import logging
import time
import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)
PROMPT_DIR = Path(__file__).parent.parent / "prompts"


def run_framework_mapper(state: dict, db_session=None, callbacks=None) -> dict:
    start_time = time.time()
    incident_id = state.get("incident_id", "unknown")
    incident_type = state.get("incident_type", "unknown")
    severity = state.get("severity", "medium")
    incident_description = state.get("incident_description", "")
    classification_metadata = state.get("classification_metadata", {})
    key_indicators = classification_metadata.get("key_indicators", [])

    try:
        prompt_template = (PROMPT_DIR / "mapper.txt").read_text()
        prompt = prompt_template.format(
            incident_type=incident_type,
            severity=severity,
            incident_description=incident_description,
            key_indicators=(
                ", ".join(key_indicators) if key_indicators else "Not specified"
            ),
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
                    content="You are a cybersecurity framework expert. Always respond with valid JSON."
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

        result = json.loads(content)
        duration_ms = int((time.time() - start_time) * 1000)

        mitre_techniques = [
            f"{t.get('technique_id')} - {t.get('technique_name')}"
            for t in result.get("mitre_attack_techniques", [])
        ]

        framework_context = {
            "nist_phases": result.get("nist_phases", []),
            "mitre_techniques": mitre_techniques,
            "owasp_categories": result.get("owasp_categories", []),
            "retrieval_sources": [],
        }

        if db_session:
            from db.database import create_audit_log

            create_audit_log(
                db_session,
                {
                    "incident_id": incident_id,
                    "agent_name": "framework_mapper",
                    "model_used": "gpt-4o-mini",
                    "input_summary": f"Type: {incident_type}, Severity: {severity}",
                    "output_summary": f"NIST: {len(framework_context['nist_phases'])} phases, MITRE: {len(mitre_techniques)} techniques",
                    "processing_time_ms": duration_ms,
                    "approval_status": "completed",
                },
            )

        return {
            **state,
            "framework_context": framework_context,
            "audit_events": state.get("audit_events", [])
            + [
                {
                    "agent": "framework_mapper",
                    "duration_ms": duration_ms,
                    "result": f"Mapped to {len(mitre_techniques)} MITRE techniques",
                }
            ],
        }
    except Exception as e:
        logger.error(f"Framework mapper error: {e}")
        return {
            **state,
            "framework_context": {
                "nist_phases": ["Detection and Analysis", "Containment"],
                "mitre_techniques": [],
                "owasp_categories": [],
                "retrieval_sources": [],
            },
            "error": str(e),
        }
