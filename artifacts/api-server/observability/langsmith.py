import os
import logging

logger = logging.getLogger(__name__)


def setup_langsmith_tracing() -> bool:
    """
    Sets up LangSmith tracing based on environment variables.
    Returns True if successfully configured, False otherwise.
    """
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        logger.info(
            "LANGSMITH_API_KEY / LANGCHAIN_API_KEY not found. LangSmith tracing is DISABLED. Using self-hosted local tracer."
        )
        # Ensure tracing environment variables are cleared
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT") or "cybershield-ai"
    os.environ["LANGCHAIN_ENDPOINT"] = (
        os.getenv("LANGCHAIN_ENDPOINT") or "https://api.smith.langchain.com"
    )

    try:
        from langsmith import Client

        Client(api_key=api_key)
        logger.info(
            f"LangSmith Tracing configured successfully. Project: {os.environ['LANGCHAIN_PROJECT']}"
        )
        return True
    except Exception as e:
        logger.error(
            f"Error checking LangSmith client connection: {e}. Disabling LangSmith tracing."
        )
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return False
