import os
import logging
import sys
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from db.database import init_db
from routes.incidents import router as incidents_router
from routes.playbooks import router as playbooks_router
from routes.dashboard import router as dashboard_router
from routes.audit import router as audit_router
from routes.reports import router as reports_router

from observability.langsmith import setup_langsmith_tracing
from security.headers import SecurityHeadersMiddleware
from security.rate_limit import RateLimitMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

_rag_initialized = False
_agents_ready = False
_langsmith_enabled = False


def initialize_chroma_rag():
    """Initializes ChromaDB and ingests RAG documentation files."""
    try:
        from rag.chroma_service import ChromaService
        from rag.embedding_service import OpenAIEmbeddingService
        from rag.ingestion_service import IngestionService

        chroma = ChromaService()
        embedding = OpenAIEmbeddingService()
        ingestion = IngestionService(chroma, embedding)

        # Clear collection and re-ingest to keep fresh
        chroma.delete_all()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        rag_data_dir = os.path.join(base_dir, "rag", "rag_data")

        if os.path.exists(rag_data_dir):
            for filename in os.listdir(rag_data_dir):
                file_path = os.path.join(rag_data_dir, filename)
                if os.path.isfile(file_path) and filename.endswith(
                    (".txt", ".pdf", ".md")
                ):
                    count = ingestion.ingest_file(file_path)
                    logger.info(
                        f"Ingested {count} chunks from {filename} into ChromaDB."
                    )
            return True
        else:
            logger.warning(f"RAG data directory not found at: {rag_data_dir}")
            return False
    except Exception as e:
        logger.error(f"Failed to initialize Chroma RAG: {e}", exc_info=True)
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _rag_initialized, _agents_ready, _langsmith_enabled
    logger.info("CyberShield AI starting up...")

    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"DB init error: {e}")

    # Initialize persistent ChromaDB RAG
    _rag_initialized = initialize_chroma_rag()

    # Try setting up LangSmith Tracing
    _langsmith_enabled = setup_langsmith_tracing()

    openai_key = os.getenv("OPENAI_API_KEY")
    _agents_ready = bool(openai_key)
    if _agents_ready:
        logger.info("Agents ready (OpenAI key configured)")
    else:
        logger.warning(
            "OPENAI_API_KEY not set — add it in Secrets to enable agent pipeline"
        )

    yield
    logger.info("CyberShield AI shutting down")


app = FastAPI(
    title="CyberShield AI",
    description=(
        "Agentic Incident Response Playbook Generator. "
        "Six AI agents: Classifier → Framework Mapper → RAG Retrieval → "
        "Playbook Generator → Compliance Reviewer → Regenerator. "
        "ChromaDB persistent vector store & LangSmith tracing."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/api/healthz", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "rag_initialized": _rag_initialized,
        "agents_ready": _agents_ready,
        "langsmith_enabled": _langsmith_enabled,
        "tracing": "langsmith" if _langsmith_enabled else "self-hosted-sqlite",
    }


app.include_router(incidents_router)
app.include_router(playbooks_router)
app.include_router(dashboard_router)
app.include_router(audit_router)
app.include_router(reports_router)

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
