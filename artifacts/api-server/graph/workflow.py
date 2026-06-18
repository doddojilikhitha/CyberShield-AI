import logging
from typing import Literal, cast, Any

from langgraph.graph import StateGraph, END

from graph.state import IncidentState
from agents.incident_classifier import run_incident_classifier
from agents.framework_mapper import run_framework_mapper
from agents.rag_retrieval import run_rag_retrieval
from agents.playbook_generator import run_playbook_generator
from agents.compliance_reviewer import run_compliance_reviewer
from agents.playbook_regenerator import run_playbook_regenerator

logger = logging.getLogger(__name__)


def route_after_review(state: IncidentState) -> Literal["regenerate", "end"]:
    review_status = state.get("review_status", "pending_review")
    reviewer_feedback = state.get("reviewer_feedback")
    if review_status == "rejected" and reviewer_feedback:
        return "regenerate"
    return "end"


def build_workflow(db_session=None, callbacks=None):
    cb = callbacks or []

    def classify(state: IncidentState) -> IncidentState:
        return cast(IncidentState, run_incident_classifier(cast(dict, state), db_session, cb))

    def map_frameworks(state: IncidentState) -> IncidentState:
        return cast(IncidentState, run_framework_mapper(cast(dict, state), db_session, cb))

    def retrieve_rag(state: IncidentState) -> IncidentState:
        return cast(IncidentState, run_rag_retrieval(cast(dict, state), db_session))

    def generate_playbook(state: IncidentState) -> IncidentState:
        return cast(IncidentState, run_playbook_generator(cast(dict, state), db_session, cb))

    def review_compliance(state: IncidentState) -> IncidentState:
        return cast(IncidentState, run_compliance_reviewer(cast(dict, state), db_session, cb))

    def regenerate_playbook(state: IncidentState) -> IncidentState:
        return cast(IncidentState, run_playbook_regenerator(cast(dict, state), db_session, cb))

    graph = StateGraph(IncidentState)
    graph.add_node("classify", classify)
    graph.add_node("map_frameworks", map_frameworks)
    graph.add_node("retrieve_rag", retrieve_rag)
    graph.add_node("generate_playbook", generate_playbook)
    graph.add_node("review_compliance", review_compliance)
    graph.add_node("regenerate_playbook", regenerate_playbook)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "map_frameworks")
    graph.add_edge("map_frameworks", "retrieve_rag")
    graph.add_edge("retrieve_rag", "generate_playbook")
    graph.add_edge("generate_playbook", "review_compliance")
    graph.add_conditional_edges(
        "review_compliance",
        route_after_review,
        {"regenerate": "regenerate_playbook", "end": END},
    )
    graph.add_edge("regenerate_playbook", END)

    return graph.compile()


def _make_tracer(incident_id: str, db_session):
    """Create a CyberShieldTracer if db_session available."""
    if db_session is None:
        return []
    try:
        from utils.tracer import CyberShieldTracer

        return [CyberShieldTracer(incident_id=incident_id, db_session=db_session)]
    except Exception as e:
        logger.warning(f"Could not create tracer: {e}")
        return []


def run_generation_workflow(incident_data: dict, db_session=None) -> dict:
    incident_id = incident_data.get("incident_id", "unknown")
    callbacks = _make_tracer(incident_id, db_session)
    workflow = build_workflow(db_session, callbacks)

    initial_state: IncidentState = {
        "incident_id": incident_id,
        "incident_description": incident_data["incident_description"],
        "incident_type": None,
        "severity": None,
        "analyst_id": incident_data.get("analyst_name"),
        "framework_context": None,
        "retrieved_context": None,
        "generated_playbook": None,
        "revised_playbook": None,
        "compliance_notes": None,
        "review_status": "generating",
        "reviewer_feedback": None,
        "processing_time": None,
        "generation_duration_ms": None,
        "regeneration_attempt_count": 0,
        "approval_timestamp": None,
        "audit_events": [],
        "created_at": None,
        "updated_at": None,
        "error": None,
    }
    result = workflow.invoke(initial_state)
    return dict(result)


def run_regeneration_workflow(incident_data: dict, db_session=None) -> dict:
    incident_id = incident_data.get("incident_id", "unknown")
    callbacks = _make_tracer(incident_id, db_session)
    workflow = build_workflow(db_session, callbacks)

    initial_state = cast(IncidentState, {
        **incident_data,
        "review_status": "rejected",
    })
    result = workflow.invoke(initial_state)
    return dict(result)
