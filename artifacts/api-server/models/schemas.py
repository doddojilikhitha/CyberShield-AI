from typing import Optional
from pydantic import BaseModel, Field


class CreateIncidentRequest(BaseModel):
    incident_description: str = Field(min_length=10)
    analyst_name: str
    incident_source: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")


class GeneratePlaybookRequest(BaseModel):
    incident_id: str


class ApprovePlaybookRequest(BaseModel):
    incident_id: str
    analyst_id: str


class RejectPlaybookRequest(BaseModel):
    incident_id: str
    analyst_id: str
    feedback: str = Field(min_length=5)


class RegeneratePlaybookRequest(BaseModel):
    incident_id: str


class FrameworkContext(BaseModel):
    nist_phases: list[str] = []
    mitre_techniques: list[str] = []
    owasp_categories: list[str] = []
    retrieval_sources: list[str] = []


class IncidentResponse(BaseModel):
    incident_id: str
    incident_description: str
    analyst_name: str
    incident_source: Optional[str] = None
    priority: str
    status: str
    created_at: str
    updated_at: Optional[str] = None


class PlaybookResponse(BaseModel):
    incident_id: str
    incident_type: Optional[str] = None
    severity: Optional[str] = None
    framework_context: Optional[FrameworkContext] = None
    generated_playbook: Optional[str] = None
    revised_playbook: Optional[str] = None
    review_status: str
    reviewer_feedback: Optional[str] = None
    processing_time: Optional[float] = None
    generation_duration_ms: Optional[int] = None
    regeneration_attempt_count: Optional[int] = None
    approval_timestamp: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RecentIncidentItem(BaseModel):
    incident_id: str
    description: str
    status: str
    priority: Optional[str] = None
    created_at: str


class AgentStats(BaseModel):
    classifier_runs: int = 0
    mapper_runs: int = 0
    rag_runs: int = 0
    generator_runs: int = 0
    reviewer_runs: int = 0
    regenerator_runs: int = 0


class DashboardMetrics(BaseModel):
    total_incidents: int
    approved_playbooks: int
    rejected_playbooks: int
    pending_review: int
    avg_generation_time_ms: float
    recent_incidents: list[RecentIncidentItem]
    agent_stats: AgentStats


class AuditLog(BaseModel):
    id: str
    incident_id: str
    agent_name: str
    timestamp: str
    model_used: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    processing_time_ms: Optional[int] = None
    approval_status: Optional[str] = None


class ApprovalMetadata(BaseModel):
    analyst_id: Optional[str] = None
    approval_timestamp: Optional[str] = None
    regeneration_attempts: Optional[int] = None


class IncidentReport(BaseModel):
    incident_id: str
    incident_summary: str
    analyst_name: Optional[str] = None
    classification: Optional[str] = None
    severity: Optional[str] = None
    nist_mapping: list[str] = []
    mitre_mapping: list[str] = []
    owasp_guidance: list[str] = []
    final_playbook: Optional[str] = None
    approval_metadata: Optional[ApprovalMetadata] = None
    audit_summary: list[AuditLog] = []
    created_at: Optional[str] = None
    approved_at: Optional[str] = None


class HealthStatus(BaseModel):
    status: str
    version: str = "1.0.0"
    rag_initialized: bool = False
    agents_ready: bool = False


class ErrorResponse(BaseModel):
    detail: str
