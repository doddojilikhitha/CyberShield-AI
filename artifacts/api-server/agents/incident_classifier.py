import json
import logging
import time
import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)
PROMPT_DIR = Path(__file__).parent.parent / "prompts"


def run_incident_classifier(state: dict, db_session=None, callbacks=None) -> dict:
    start_time = time.time()
    incident_id = state.get("incident_id", "unknown")
    incident_description = state.get("incident_description", "")

    try:
        prompt_template = (PROMPT_DIR / "classifier.txt").read_text()
        prompt = prompt_template.format(incident_description=incident_description)

        llm = ChatOpenAI(
            model=os.getenv("FAST_LLM_MODEL", "gpt-4o-mini"),
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),  # type: ignore[call-arg]
            callbacks=callbacks or [],
        )
        response = llm.invoke(
            [
                SystemMessage(
                    content="You are a cybersecurity incident classification expert. Always respond with valid JSON."
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

        if db_session:
            from db.database import create_audit_log

            create_audit_log(
                db_session,
                {
                    "incident_id": incident_id,
                    "agent_name": "incident_classifier",
                    "model_used": "gpt-4o-mini",
                    "input_summary": incident_description[:200],
                    "output_summary": f"Type: {result.get('incident_type')}, Severity: {result.get('severity')}",
                    "processing_time_ms": duration_ms,
                    "approval_status": "completed",
                },
            )

        return {
            **state,
            "incident_type": result.get("incident_type", "unknown"),
            "severity": result.get("severity", "medium"),
            "classification_metadata": result,
            "audit_events": state.get("audit_events", [])
            + [
                {
                    "agent": "incident_classifier",
                    "duration_ms": duration_ms,
                    "result": f"Type: {result.get('incident_type')}, Severity: {result.get('severity')}",
                }
            ],
        }
    except Exception as e:
        logger.error(f"Incident classifier error: {e}")
        return {
            **state,
            "incident_type": "unknown",
            "severity": "medium",
            "error": str(e),
        }
