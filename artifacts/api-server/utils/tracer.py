"""
Self-hosted LangChain tracing — stores every LLM call, chain, and agent
action to SQLite so you get full observability without LangSmith.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_json(obj: Any, max_len: int = 2000) -> str:
    try:
        raw = json.dumps(obj, default=str)
        return raw[:max_len] if len(raw) > max_len else raw
    except Exception:
        return str(obj)[:max_len]


class CyberShieldTracer(BaseCallbackHandler):
    """
    Captures every LLM call and chain run for an incident, writing
    structured trace records to the local SQLite database.
    """

    def __init__(self, incident_id: str, db_session):
        super().__init__()
        self.incident_id = incident_id
        self.db = db_session
        self._runs: dict[str, dict] = {}  # run_id → metadata

    # ------------------------------------------------------------------ #
    # LLM events
    # ------------------------------------------------------------------ #

    def on_llm_start(
        self,
        serialized: dict,
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        model = (
            serialized.get("kwargs", {}).get("model_name")
            or serialized.get("id", ["", "", "unknown"])[-1]
        )
        self._runs[str(run_id)] = {
            "type": "llm",
            "model": model,
            "started_at": time.time(),
            "input": _safe_json(prompts),
        }

    def on_chat_model_start(
        self,
        serialized: dict,
        messages: list,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        model = (
            serialized.get("kwargs", {}).get("model_name")
            or serialized.get("kwargs", {}).get("model")
            or serialized.get("id", ["", "", "unknown"])[-1]
        )
        msg_texts = []
        for group in messages:
            for m in group:
                role = getattr(m, "type", "?")
                content = getattr(m, "content", "")[:500]
                msg_texts.append(f"[{role}] {content}")
        self._runs[str(run_id)] = {
            "type": "llm",
            "model": model,
            "started_at": time.time(),
            "input": "\n".join(msg_texts)[:2000],
        }

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        run = self._runs.pop(str(run_id), {})
        if not run:
            return
        elapsed_ms = int((time.time() - run.get("started_at", time.time())) * 1000)
        output = ""
        try:
            output = response.generations[0][0].text[:2000]
        except Exception:
            output = _safe_json(response.dict())

        token_usage = {}
        if response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})

        self._write_trace(
            event_type="llm_call",
            agent_name=f"llm:{run.get('model', 'unknown')}",
            model_used=run.get("model"),
            input_summary=run.get("input", "")[:500],
            output_summary=output[:500],
            processing_time_ms=elapsed_ms,
            metadata={
                "token_usage": token_usage,
                "finish_reason": getattr(
                    response.generations[0][0], "generation_info", {}
                ),
            },
        )

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        run = self._runs.pop(str(run_id), {})
        elapsed_ms = int((time.time() - run.get("started_at", time.time())) * 1000)
        self._write_trace(
            event_type="llm_error",
            agent_name=f"llm:{run.get('model', 'unknown')}",
            model_used=run.get("model"),
            input_summary=run.get("input", "")[:300],
            output_summary=f"ERROR: {str(error)[:400]}",
            processing_time_ms=elapsed_ms,
            metadata={"error": str(error)},
        )

    # ------------------------------------------------------------------ #
    # Chain events
    # ------------------------------------------------------------------ #

    def on_chain_start(
        self,
        serialized: dict,
        inputs: dict,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        name = serialized.get("id", ["", "", "chain"])[-1] if serialized else "chain"
        self._runs[str(run_id)] = {
            "type": "chain",
            "name": name,
            "started_at": time.time(),
            "input": _safe_json(inputs),
        }

    def on_chain_end(
        self,
        outputs: dict,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        run = self._runs.pop(str(run_id), {})
        if not run:
            return
        elapsed_ms = int((time.time() - run.get("started_at", time.time())) * 1000)
        self._write_trace(
            event_type="chain",
            agent_name=f"chain:{run.get('name', 'unknown')}",
            input_summary=run.get("input", "")[:300],
            output_summary=_safe_json(outputs)[:400],
            processing_time_ms=elapsed_ms,
        )

    # ------------------------------------------------------------------ #
    # Tool events (for agent tools)
    # ------------------------------------------------------------------ #

    def on_tool_start(
        self,
        serialized: dict,
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        tool_name = (
            serialized.get("name", "unknown_tool") if serialized else "unknown_tool"
        )
        self._runs[str(run_id)] = {
            "type": "tool",
            "name": tool_name,
            "started_at": time.time(),
            "input": input_str[:500],
        }

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        run = self._runs.pop(str(run_id), {})
        if not run:
            return
        elapsed_ms = int((time.time() - run.get("started_at", time.time())) * 1000)
        self._write_trace(
            event_type="tool",
            agent_name=f"tool:{run.get('name', 'unknown')}",
            input_summary=run.get("input", "")[:300],
            output_summary=str(output)[:400],
            processing_time_ms=elapsed_ms,
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _write_trace(
        self,
        event_type: str,
        agent_name: str,
        input_summary: str = "",
        output_summary: str = "",
        processing_time_ms: int = 0,
        model_used: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        try:
            from db.database import create_trace

            create_trace(
                self.db,
                {
                    "incident_id": self.incident_id,
                    "event_type": event_type,
                    "agent_name": agent_name,
                    "model_used": model_used,
                    "input_summary": input_summary,
                    "output_summary": output_summary,
                    "processing_time_ms": processing_time_ms,
                    "metadata": json.dumps(metadata or {}),
                    "timestamp": _now(),
                },
            )
        except Exception as e:
            logger.debug(f"Trace write error (non-fatal): {e}")
