import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:///./cybershield.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id TEXT PRIMARY KEY,
                incident_description TEXT NOT NULL,
                analyst_name TEXT NOT NULL,
                incident_source TEXT,
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'submitted',
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS playbooks (
                incident_id TEXT PRIMARY KEY,
                incident_type TEXT,
                severity TEXT,
                framework_context TEXT,
                generated_playbook TEXT,
                revised_playbook TEXT,
                review_status TEXT NOT NULL DEFAULT 'pending_review',
                reviewer_feedback TEXT,
                processing_time REAL,
                generation_duration_ms INTEGER,
                regeneration_attempt_count INTEGER DEFAULT 0,
                approval_timestamp TEXT,
                analyst_id TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                model_used TEXT,
                input_summary TEXT,
                output_summary TEXT,
                processing_time_ms INTEGER,
                approval_status TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS traces (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                model_used TEXT,
                input_summary TEXT,
                output_summary TEXT,
                processing_time_ms INTEGER,
                metadata TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS reports (
                incident_id TEXT PRIMARY KEY,
                report_data TEXT NOT NULL,
                pdf_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS workflow_runs (
                run_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                status TEXT NOT NULL,
                steps_completed TEXT,
                duration_ms INTEGER,
                started_at TEXT NOT NULL,
                completed_at TEXT
            )
        """))
        conn.commit()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Incident operations ---


def create_incident(db: Session, data: dict) -> dict:
    incident_id = str(uuid.uuid4())
    created_at = now_iso()
    db.execute(
        text("""
        INSERT INTO incidents (incident_id, incident_description, analyst_name, incident_source, priority, status, created_at)
        VALUES (:incident_id, :incident_description, :analyst_name, :incident_source, :priority, :status, :created_at)
    """),
        {
            "incident_id": incident_id,
            "incident_description": data["incident_description"],
            "analyst_name": data["analyst_name"],
            "incident_source": data.get("incident_source"),
            "priority": data.get("priority", "medium"),
            "status": "submitted",
            "created_at": created_at,
        },
    )
    db.commit()
    res = get_incident(db, incident_id)
    assert res is not None
    return res


def get_incident(db: Session, incident_id: str) -> Optional[dict]:
    row = db.execute(
        text("SELECT * FROM incidents WHERE incident_id = :id"), {"id": incident_id}
    ).fetchone()
    if not row:
        return None
    return dict(row._mapping)


def list_incidents(db: Session) -> list[dict]:
    rows = db.execute(
        text("SELECT * FROM incidents ORDER BY created_at DESC")
    ).fetchall()
    return [dict(r._mapping) for r in rows]


def update_incident_status(db: Session, incident_id: str, status: str):
    db.execute(
        text("""
        UPDATE incidents SET status = :status, updated_at = :updated_at
        WHERE incident_id = :incident_id
    """),
        {"status": status, "updated_at": now_iso(), "incident_id": incident_id},
    )
    db.commit()


# --- Playbook operations ---


def create_or_update_playbook(db: Session, incident_id: str, data: dict):
    existing = get_playbook(db, incident_id)
    if existing:
        set_clauses = ", ".join([f"{k} = :{k}" for k in data.keys()])
        data["incident_id"] = incident_id
        data["updated_at"] = now_iso()
        db.execute(
            text(
                f"UPDATE playbooks SET {set_clauses}, updated_at = :updated_at WHERE incident_id = :incident_id"
            ),
            data,
        )
    else:
        data["incident_id"] = incident_id
        data.setdefault("created_at", now_iso())
        data.setdefault("updated_at", now_iso())
        data.setdefault("regeneration_attempt_count", 0)
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f":{k}" for k in data.keys()])
        db.execute(
            text(f"INSERT INTO playbooks ({columns}) VALUES ({placeholders})"), data
        )
    db.commit()


def get_playbook(db: Session, incident_id: str) -> Optional[dict]:
    row = db.execute(
        text("SELECT * FROM playbooks WHERE incident_id = :id"), {"id": incident_id}
    ).fetchone()
    if not row:
        return None
    d = dict(row._mapping)
    if d.get("framework_context") and isinstance(d["framework_context"], str):
        try:
            d["framework_context"] = json.loads(d["framework_context"])
        except Exception:
            d["framework_context"] = None
    return d


# --- Audit log operations ---


def create_audit_log(db: Session, data: dict) -> dict:
    log_id = str(uuid.uuid4())
    db.execute(
        text("""
        INSERT INTO audit_logs (id, incident_id, agent_name, timestamp, model_used, input_summary, output_summary, processing_time_ms, approval_status)
        VALUES (:id, :incident_id, :agent_name, :timestamp, :model_used, :input_summary, :output_summary, :processing_time_ms, :approval_status)
    """),
        {
            "id": log_id,
            "incident_id": data["incident_id"],
            "agent_name": data["agent_name"],
            "timestamp": data.get("timestamp", now_iso()),
            "model_used": data.get("model_used"),
            "input_summary": data.get("input_summary"),
            "output_summary": data.get("output_summary"),
            "processing_time_ms": data.get("processing_time_ms"),
            "approval_status": data.get("approval_status"),
        },
    )
    db.commit()
    return {"id": log_id, **data}


def get_audit_logs(
    db: Session, incident_id: Optional[str] = None, limit: int = 50
) -> list[dict]:
    if incident_id:
        rows = db.execute(
            text(
                "SELECT * FROM audit_logs WHERE incident_id = :id ORDER BY timestamp DESC LIMIT :limit"
            ),
            {"id": incident_id, "limit": limit},
        ).fetchall()
    else:
        rows = db.execute(
            text("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT :limit"),
            {"limit": limit},
        ).fetchall()
    return [dict(r._mapping) for r in rows]


# --- Trace operations (self-hosted LangSmith alternative) ---


def create_trace(db: Session, data: dict) -> dict:
    trace_id = str(uuid.uuid4())
    db.execute(
        text("""
        INSERT INTO traces (id, incident_id, event_type, agent_name, timestamp, model_used,
                            input_summary, output_summary, processing_time_ms, metadata)
        VALUES (:id, :incident_id, :event_type, :agent_name, :timestamp, :model_used,
                :input_summary, :output_summary, :processing_time_ms, :metadata)
    """),
        {
            "id": trace_id,
            "incident_id": data["incident_id"],
            "event_type": data.get("event_type", "unknown"),
            "agent_name": data.get("agent_name", "unknown"),
            "timestamp": data.get("timestamp", now_iso()),
            "model_used": data.get("model_used"),
            "input_summary": data.get("input_summary", ""),
            "output_summary": data.get("output_summary", ""),
            "processing_time_ms": data.get("processing_time_ms", 0),
            "metadata": data.get("metadata", "{}"),
        },
    )
    db.commit()
    return {"id": trace_id, **data}


def get_traces(
    db: Session, incident_id: Optional[str] = None, limit: int = 200
) -> list[dict]:
    if incident_id:
        rows = db.execute(
            text(
                "SELECT * FROM traces WHERE incident_id = :id ORDER BY timestamp ASC LIMIT :limit"
            ),
            {"id": incident_id, "limit": limit},
        ).fetchall()
    else:
        rows = db.execute(
            text("SELECT * FROM traces ORDER BY timestamp DESC LIMIT :limit"),
            {"limit": limit},
        ).fetchall()
    return [dict(r._mapping) for r in rows]


# --- Dashboard metrics ---


def get_dashboard_metrics(db: Session) -> dict:
    row_total = db.execute(text("SELECT COUNT(*) as c FROM incidents")).fetchone()
    total = row_total.c if row_total is not None else 0

    row_approved = db.execute(
        text("SELECT COUNT(*) as c FROM playbooks WHERE review_status = 'approved'")
    ).fetchone()
    approved = row_approved.c if row_approved is not None else 0

    row_rejected = db.execute(
        text("SELECT COUNT(*) as c FROM playbooks WHERE review_status = 'rejected'")
    ).fetchone()
    rejected = row_rejected.c if row_rejected is not None else 0

    row_pending = db.execute(
        text(
            "SELECT COUNT(*) as c FROM playbooks WHERE review_status = 'pending_review'"
        )
    ).fetchone()
    pending = row_pending.c if row_pending is not None else 0

    avg_row = db.execute(
        text(
            "SELECT AVG(generation_duration_ms) as avg FROM playbooks WHERE generation_duration_ms IS NOT NULL"
        )
    ).fetchone()
    avg_time = (avg_row.avg if avg_row is not None else 0.0) or 0.0

    recent_rows = db.execute(text("""
        SELECT i.incident_id, i.incident_description, i.priority, i.created_at,
               COALESCE(p.review_status, i.status) as status
        FROM incidents i
        LEFT JOIN playbooks p ON i.incident_id = p.incident_id
        ORDER BY i.created_at DESC LIMIT 5
    """)).fetchall()

    agent_counts = {}
    for agent in [
        "incident_classifier",
        "framework_mapper",
        "rag_retrieval",
        "playbook_generator",
        "compliance_reviewer",
        "playbook_regenerator",
    ]:
        row = db.execute(
            text("SELECT COUNT(*) as c FROM audit_logs WHERE agent_name = :name"),
            {"name": agent},
        ).fetchone()
        agent_counts[agent] = row.c if row is not None else 0

    return {
        "total_incidents": total,
        "approved_playbooks": approved,
        "rejected_playbooks": rejected,
        "pending_review": pending,
        "avg_generation_time_ms": avg_time,
        "recent_incidents": [
            {
                "incident_id": r.incident_id,
                "description": r.incident_description[:100],
                "status": r.status,
                "priority": r.priority,
                "created_at": r.created_at,
            }
            for r in recent_rows
        ],
        "agent_stats": {
            "classifier_runs": agent_counts.get("incident_classifier", 0),
            "mapper_runs": agent_counts.get("framework_mapper", 0),
            "rag_runs": agent_counts.get("rag_retrieval", 0),
            "generator_runs": agent_counts.get("playbook_generator", 0),
            "reviewer_runs": agent_counts.get("compliance_reviewer", 0),
            "regenerator_runs": agent_counts.get("playbook_regenerator", 0),
        },
    }


# --- Report operations ---


def create_or_update_report(
    db: Session, incident_id: str, report_data: dict, pdf_path: Optional[str] = None
):
    serialized = json.dumps(report_data)
    existing = db.execute(
        text("SELECT 1 FROM reports WHERE incident_id = :id"), {"id": incident_id}
    ).fetchone()
    if existing:
        db.execute(
            text("""
            UPDATE reports SET report_data = :report_data, pdf_path = :pdf_path, updated_at = :updated_at
            WHERE incident_id = :incident_id
        """),
            {
                "report_data": serialized,
                "pdf_path": pdf_path,
                "updated_at": now_iso(),
                "incident_id": incident_id,
            },
        )
    else:
        db.execute(
            text("""
            INSERT INTO reports (incident_id, report_data, pdf_path, created_at, updated_at)
            VALUES (:incident_id, :report_data, :pdf_path, :created_at, :updated_at)
        """),
            {
                "incident_id": incident_id,
                "report_data": serialized,
                "pdf_path": pdf_path,
                "created_at": now_iso(),
                "updated_at": now_iso(),
            },
        )
    db.commit()


def get_report_db(db: Session, incident_id: str) -> Optional[dict]:
    row = db.execute(
        text("SELECT * FROM reports WHERE incident_id = :id"), {"id": incident_id}
    ).fetchone()
    if not row:
        return None
    d = dict(row._mapping)
    try:
        d["report_data"] = json.loads(d["report_data"])
    except Exception:
        d["report_data"] = {}
    return d


# --- Workflow Run operations ---


def create_workflow_run(
    db: Session, run_id: str, incident_id: str, status: str
) -> dict:
    started_at = now_iso()
    db.execute(
        text("""
        INSERT INTO workflow_runs (run_id, incident_id, status, started_at)
        VALUES (:run_id, :incident_id, :status, :started_at)
    """),
        {
            "run_id": run_id,
            "incident_id": incident_id,
            "status": status,
            "started_at": started_at,
        },
    )
    db.commit()
    return {
        "run_id": run_id,
        "incident_id": incident_id,
        "status": status,
        "started_at": started_at,
    }


def update_workflow_run(db: Session, run_id: str, data: dict):
    set_clauses = ", ".join([f"{k} = :{k}" for k in data.keys()])
    data["run_id"] = run_id
    if "steps_completed" in data and not isinstance(data["steps_completed"], str):
        data["steps_completed"] = json.dumps(data["steps_completed"])
    db.execute(
        text(f"UPDATE workflow_runs SET {set_clauses} WHERE run_id = :run_id"), data
    )
    db.commit()


def get_workflow_runs(db: Session, incident_id: Optional[str] = None) -> list[dict]:
    if incident_id:
        rows = db.execute(
            text(
                "SELECT * FROM workflow_runs WHERE incident_id = :id ORDER BY started_at DESC"
            ),
            {"id": incident_id},
        ).fetchall()
    else:
        rows = db.execute(
            text("SELECT * FROM workflow_runs ORDER BY started_at DESC")
        ).fetchall()

    results = []
    for r in rows:
        d = dict(r._mapping)
        if d.get("steps_completed"):
            try:
                d["steps_completed"] = json.loads(d["steps_completed"])
            except Exception:
                d["steps_completed"] = []
        results.append(d)
    return results
