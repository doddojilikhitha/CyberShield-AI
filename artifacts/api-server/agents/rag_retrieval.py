import logging
import time

from rag.chroma_service import ChromaService
from rag.embedding_service import OpenAIEmbeddingService
from rag.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


def run_rag_retrieval(state: dict, db_session=None) -> dict:
    start_time = time.time()
    incident_id = state.get("incident_id", "unknown")
    incident_type = state.get("incident_type", "unknown")
    severity = state.get("severity", "medium")
    incident_description = state.get("incident_description", "")
    framework_context = state.get("framework_context", {})

    try:
        mitre_techniques = framework_context.get("mitre_techniques", [])
        query = f"{incident_type} incident response {severity} severity {incident_description[:200]}"
        if mitre_techniques:
            query += f" techniques: {', '.join(mitre_techniques[:3])}"

        chroma = ChromaService()
        embedding = OpenAIEmbeddingService()
        retrieval = RetrievalService(chroma, embedding)
        context, sources, scores = retrieval.retrieve_context(query, k=5)

        duration_ms = int((time.time() - start_time) * 1000)

        if framework_context and sources:
            framework_context["retrieval_sources"] = sources

        if db_session:
            from db.database import create_audit_log

            create_audit_log(
                db_session,
                {
                    "incident_id": incident_id,
                    "agent_name": "rag_retrieval",
                    "model_used": "text-embedding-3-small",
                    "input_summary": query[:200],
                    "output_summary": f"Retrieved {len(context)} chars from sources: {', '.join(sources)}",
                    "processing_time_ms": duration_ms,
                    "approval_status": "completed",
                },
            )

        return {
            **state,
            "retrieved_context": context,
            "framework_context": framework_context,
            "audit_events": state.get("audit_events", [])
            + [
                {
                    "agent": "rag_retrieval",
                    "duration_ms": duration_ms,
                    "result": f"Retrieved from: {', '.join(sources)}",
                }
            ],
        }
    except Exception as e:
        logger.error(f"RAG retrieval error: {e}")
        return {
            **state,
            "retrieved_context": "Fallback: Apply standard incident response procedures per NIST SP 800-61.",
            "error": str(e),
        }
