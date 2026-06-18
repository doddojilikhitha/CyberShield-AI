from typing import Optional, TypedDict


class IncidentState(TypedDict, total=False):
    incident_id: str
    incident_description: str
    incident_type: Optional[str]
    severity: Optional[str]
    analyst_id: Optional[str]
    framework_context: Optional[dict]
    retrieved_context: Optional[str]
    generated_playbook: Optional[str]
    revised_playbook: Optional[str]
    compliance_notes: Optional[str]
    review_status: str
    reviewer_feedback: Optional[str]
    processing_time: Optional[float]
    generation_duration_ms: Optional[int]
    regeneration_attempt_count: int
    approval_timestamp: Optional[str]
    audit_events: list
    created_at: Optional[str]
    updated_at: Optional[str]
    error: Optional[str]
