import os
import pytest
from unittest.mock import patch, MagicMock

from observability.langsmith import setup_langsmith_tracing
from observability.tracing import get_tracing_callbacks
from utils.tracer import CyberShieldTracer


@pytest.fixture
def clean_env():
    """Backup and clean environment variables before each test."""
    backup = dict(os.environ)
    for key in [
        "LANGSMITH_API_KEY",
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_PROJECT",
        "LANGCHAIN_ENDPOINT",
    ]:
        if key in os.environ:
            del os.environ[key]
    yield
    os.environ.clear()
    os.environ.update(backup)


def test_langsmith_config_loading_no_keys(clean_env):
    """Verify setup fails when no API keys are present."""
    result = setup_langsmith_tracing()
    assert result is False
    assert os.getenv("LANGCHAIN_TRACING_V2") == "false"


@patch("langsmith.Client")
def test_langsmith_config_loading_success(mock_client, clean_env):
    """Verify setup succeeds and sets environment variables when key is provided."""
    os.environ["LANGSMITH_API_KEY"] = "mock_key_123"
    result = setup_langsmith_tracing()
    assert result is True
    assert os.getenv("LANGCHAIN_TRACING_V2") == "true"
    assert os.getenv("LANGCHAIN_PROJECT") == "cybershield-ai"
    assert os.getenv("LANGCHAIN_ENDPOINT") == "https://api.smith.langchain.com"
    mock_client.assert_called_once_with(api_key="mock_key_123")


@patch("langsmith.Client")
def test_langsmith_graceful_failure_handling(mock_client, clean_env):
    """Verify setup handles exceptions from client initialization gracefully."""
    os.environ["LANGSMITH_API_KEY"] = "mock_key_123"
    mock_client.side_effect = Exception("Connection Refused")

    result = setup_langsmith_tracing()
    assert result is False
    assert os.getenv("LANGCHAIN_TRACING_V2") == "false"


def test_tracing_callbacks_selection(clean_env):
    """Verify callbacks list contains local tracer when LangSmith is disabled."""
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    mock_db = MagicMock()

    callbacks = get_tracing_callbacks(incident_id="test-incident", db_session=mock_db)
    assert len(callbacks) == 1
    assert isinstance(callbacks[0], CyberShieldTracer)


def test_tracing_callbacks_selection_active_langsmith(clean_env):
    """Verify local tracer is skipped when LangSmith tracing is active."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    mock_db = MagicMock()

    callbacks = get_tracing_callbacks(incident_id="test-incident", db_session=mock_db)
    assert len(callbacks) == 0


def test_callback_event_tracing_handlers(clean_env):
    """Verify that CyberShieldTracer event handlers trace all runs and write to DB."""
    mock_db = MagicMock()
    tracer = CyberShieldTracer(incident_id="test-incident-uuid", db_session=mock_db)

    # 1. Workflow / Chain Tracing
    run_id_chain = "11111111-2222-3333-4444-555555555555"
    serialized_chain = {"id": ["langgraph", "workflow"]}
    inputs_chain = {"incident_description": "suspicious file transfer"}
    tracer.on_chain_start(serialized_chain, inputs_chain, run_id=run_id_chain)
    assert run_id_chain in tracer._runs

    outputs_chain = {"generated_playbook": "Containment checklist"}
    with patch("db.database.create_trace") as mock_create_trace:
        tracer.on_chain_end(outputs_chain, run_id=run_id_chain)
        assert mock_create_trace.called
        event = mock_create_trace.call_args[0][1]
        assert event["event_type"] == "chain"
        assert "workflow" in event["agent_name"]

    # 2. LLM / Agent Tracing
    run_id_llm = "22222222-3333-4444-5555-666666666666"
    serialized_llm = {"kwargs": {"model_name": "gpt-4o-mini"}}
    prompts_llm = ["Analyze anomalous activity:"]
    tracer.on_llm_start(serialized_llm, prompts_llm, run_id=run_id_llm)
    assert run_id_llm in tracer._runs

    # Mock LLMResult response
    from langchain_core.outputs import LLMResult, Generation

    generation = Generation(text="Detected Ransomware threat vector.")
    response = LLMResult(
        generations=[[generation]], llm_output={"token_usage": {"total_tokens": 120}}
    )

    with patch("db.database.create_trace") as mock_create_trace:
        tracer.on_llm_end(response, run_id=run_id_llm)
        assert mock_create_trace.called
        event = mock_create_trace.call_args[0][1]
        assert event["event_type"] == "llm_call"
        assert event["model_used"] == "gpt-4o-mini"

    # 3. Retrieval / Tool Tracing
    run_id_tool = "33333333-4444-5555-6666-777777777777"
    serialized_tool = {"name": "rag_retrieval_tool"}
    input_str_tool = "phishing incident response"
    tracer.on_tool_start(serialized_tool, input_str_tool, run_id=run_id_tool)
    assert run_id_tool in tracer._runs

    output_tool = "NIST SP 800-61 Phishing Containment Guidelines"
    with patch("db.database.create_trace") as mock_create_trace:
        tracer.on_tool_end(output_tool, run_id=run_id_tool)
        assert mock_create_trace.called
        event = mock_create_trace.call_args[0][1]
        assert event["event_type"] == "tool"
        assert "rag_retrieval_tool" in event["agent_name"]
