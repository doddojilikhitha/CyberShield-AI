import os
import logging
from typing import List, Any
from utils.tracer import CyberShieldTracer

logger = logging.getLogger(__name__)


def get_tracing_callbacks(incident_id: str, db_session=None) -> List[Any]:
    """
    Returns the appropriate LangChain callbacks for tracing.
    If LangSmith is configured, we can let LangChain trace automatically or append standard handlers.
    If LangSmith is absent, we append our custom CyberShieldTracer which writes traces locally.
    """
    callbacks = []

    # 1. Custom SQLite tracing fallback
    # If LANGCHAIN_TRACING_V2 environment variable is not explicitly true, use self-hosted
    is_langsmith_active = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

    if not is_langsmith_active and db_session is not None:
        try:
            local_tracer = CyberShieldTracer(
                incident_id=incident_id, db_session=db_session
            )
            callbacks.append(local_tracer)
            logger.info(
                f"Initialized local SQLite trace handler for incident: {incident_id}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize local SQLite trace handler: {e}")

    return callbacks
