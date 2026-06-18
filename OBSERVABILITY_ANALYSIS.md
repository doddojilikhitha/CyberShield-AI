# Observability & Trace Analysis — CyberShield AI

This analysis outlines the tracing, logging, and operational monitoring configurations implemented in **CyberShield AI**. The project leverages a robust, two-tier observability framework designed to support enterprise-grade cloud analytics while ensuring reliable local failover mechanics.

---

## 🛰️ Multi-Tier Observability Architecture

Observability in CyberShield AI is structured into two complementary layers, determined automatically at runtime based on environment key configuration:

```
                  ┌───────────────────────────────┐
                  │   LangGraph Agent Execution   │
                  └───────────────┬───────────────┘
                                  │
                   Is LANGSMITH_API_KEY Configured?
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
                YES                                NO
                 │                                 │
                 ▼                                 ▼
   ┌───────────────────────────┐     ┌───────────────────────────┐
   │    LangSmith Cloud Tracing │     │   Self-Hosted SQLite      │
   │   (Enterprise Monitoring)  │     │   Custom Trace Callback   │
   └───────────────────────────┘     └───────────────────────────┘
```

---

## ☁️ Tier 1: LangSmith Cloud Integration

If active, the system routes telemetry directly to the **LangSmith** developer platform:

### 1. Initialization ([langsmith.py](file:///c:/Users/likhi/Downloads/Cyber-Secure-Link/Cyber-Secure-Link/artifacts/api-server/observability/langsmith.py))
* Checks for `LANGSMITH_API_KEY` or `LANGCHAIN_API_KEY`.
* Configures LangChain core tracing variables:
  * `LANGCHAIN_TRACING_V2=true`
  * `LANGCHAIN_PROJECT` (defaults to `cybershield-ai`)
  * `LANGCHAIN_ENDPOINT` (defaults to `https://api.smith.langchain.com`)
* Initializes the `langsmith.Client` to confirm the cloud connection.

### 2. Auto-Tracing Capabilities
* Once configured, the SDK automatically hooks into all LangGraph execution chains, capturing full prompt templates, token consumption details, and generation latency without requiring manual callbacks.

---

## 💾 Tier 2: Self-Hosted Local SQLite Tracer

If LangSmith API keys are not provided, CyberShield AI automatically falls back to an independent, self-hosted local tracing suite. This is powered by a custom LangChain callback handler:

### 1. Custom Callback Handler ([tracer.py](file:///c:/Users/likhi/Downloads/Cyber-Secure-Link/Cyber-Secure-Link/artifacts/api-server/utils/tracer.py))
The `CyberShieldTracer` class extends LangChain's `BaseCallbackHandler` to capture runtime events during agent runs:
* **LLM Calls (`on_chat_model_start` / `on_llm_end`)**: Intercepts chat prompts, formats role tags (`[system]`, `[human]`), and calculates elapsed execution time in milliseconds.
* **Exceptions (`on_llm_error`)**: Catches API execution failures, saving the complete stack trace and error status while redacting sensitive details.
* **Chain Steps (`on_chain_start` / `on_chain_end`)**: Documents transitions between LangGraph nodes, mapping inputs and outputs as structured JSON payloads.
* **Tool Running (`on_tool_start` / `on_tool_end`)**: Logs tool actions, input strings, and return values (e.g., framework mapper lookups).

### 2. Trace Records Database Structure
Telemetry captures are stored locally inside the `traces` table in the SQLite database (`cybershield.db`):
* `id`: Unique trace run UUID.
* `incident_id`: The identifier of the associated incident.
* `event_type`: Type of event (`llm_call`, `chain`, `tool`, `llm_error`).
* `agent_name`: Name of the active node or model (e.g., `llm:gemini-2.5-flash`).
* `model_used`: The specific model selected for execution.
* `input_summary`: Snippet of input prompts.
* `output_summary`: Snippet of the generated output.
* `processing_time_ms`: Total execution duration in milliseconds.
* `metadata`: Raw metadata dictionary containing token usages, finish reasons, or error lists.

---

## 📝 Immutable Audit Trail & Metrics

Beyond low-level step execution traces, CyberShield AI records high-level audit logs and performance metrics:

### 1. Audit Logs (`audit_logs` table)
Whenever an agent completes its task, a row is committed to the local database, providing a review trail:
* Details the agent's identity, the model used, the execution latency, and a summary of inputs/outputs.
* Records human decisions, such as approvals, rejections, reviewer feedback statements, and playbook regeneration iterations.
* This audit trail is displayed directly on the React frontend dashboard to verify system operations.

### 2. Performance Monitoring
The API router `/api/dashboard/metrics` aggregates trace data to monitor service health:
* Calculates average playbook generation latency (`AVG(generation_duration_ms)`).
* Tracks total incident counts, approved playbooks, and rejected playbooks.
* Aggregates usage metrics for each agent node (e.g., how many times the `framework_mapper` has run), identifying system bottlenecks.

---

## 🔍 RAG Ingestion Logging

The vector indexing service logs pipeline executions:
* **Splitting**: Reports how many chunks are parsed from raw files in the `rag_data` directory.
* **Ingestion**: Documents vector database updates, confirming successful vector uploads to ChromaDB.
* **Similarity Queries**: Logs ChromaDB query failures or successful retrieval mappings.
