import os
import pytest
from langsmith import Client


def test_langsmith_integration_client_connection():
    """
    Validates connection to the real LangSmith platform if API key is configured.
    Otherwise, skips the test cleanly using pytest.skip().
    """
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        pytest.skip(
            "LANGSMITH_API_KEY / LANGCHAIN_API_KEY not configured. Skipping integration tests."
        )

    try:
        # Check connection to LangSmith server
        client = Client(api_key=api_key)

        # Test creating a test run or checking connection endpoints
        # Verify that listing projects works or doesn't raise connection/auth error
        projects = list(client.list_projects())
        assert isinstance(projects, list)
    except Exception as e:
        pytest.fail(
            f"Failed to connect or validate with LangSmith platform using the provided API Key: {e}"
        )
