import logging
import math
import re
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)

RAG_DATA_DIR = Path(__file__).parent / "rag_data"

_documents: list[dict] = []
_initialized = False


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b[a-z0-9]+\b", text.lower())


def _build_index(docs: list[dict]) -> dict:
    """Build a simple TF-IDF-like inverted index."""
    idf: dict[str, float] = {}
    doc_counts: dict[str, int] = {}
    N = len(docs)

    for doc in docs:
        tokens = set(_tokenize(doc["content"]))
        for token in tokens:
            doc_counts[token] = doc_counts.get(token, 0) + 1

    for token, count in doc_counts.items():
        idf[token] = math.log((N + 1) / (count + 1)) + 1.0

    for doc in docs:
        doc_tokens = _tokenize(doc["content"])
        total = len(doc_tokens)
        freq = Counter(doc_tokens)
        doc["tf_idf"] = {t: (freq[t] / total) * idf.get(t, 1.0) for t in freq}

    return idf


def initialize_rag() -> bool:
    global _documents, _initialized
    try:
        chunks: list[dict] = []
        for file_path in sorted(RAG_DATA_DIR.glob("*.txt")):
            text = file_path.read_text(encoding="utf-8")
            paragraphs = [
                p.strip()
                for p in re.split(r"\n{2,}", text)
                if p.strip() and len(p.strip()) > 50
            ]
            for para in paragraphs:
                chunks.append(
                    {
                        "content": para,
                        "source": file_path.name,
                        "tf_idf": {},
                    }
                )
            logger.info(f"Loaded {len(paragraphs)} chunks from {file_path.name}")

        if not chunks:
            logger.warning("No documents found in rag_data/")
            return False

        _build_index(chunks)
        _documents = chunks
        _initialized = True
        logger.info(f"RAG initialized with {len(chunks)} document chunks (TF-IDF)")
        return True
    except Exception as e:
        logger.error(f"RAG initialization failed: {e}")
        return False


def retrieve_context(query: str, k: int = 5) -> tuple[str, list[str]]:
    if not _initialized or not _documents:
        return _get_fallback_context(query), ["Built-in knowledge base"]

    try:
        query_tokens = _tokenize(query)
        scores: list[tuple[float, int]] = []

        for i, doc in enumerate(_documents):
            score = 0.0
            tfidf = doc.get("tf_idf", {})
            for token in query_tokens:
                score += tfidf.get(token, 0.0)
            scores.append((score, i))

        scores.sort(reverse=True)
        top_k = [idx for _, idx in scores[:k] if _ > 0]

        if not top_k:
            top_k = [idx for _, idx in scores[:3]]

        context_parts = []
        sources = []
        for idx in top_k:
            doc = _documents[idx]
            source = doc["source"]
            context_parts.append(f"[Source: {source}]\n{doc['content']}")
            if source not in sources:
                sources.append(source)

        context = "\n\n---\n\n".join(context_parts)
        return context, sources
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return _get_fallback_context(query), ["Built-in knowledge base"]


def _get_fallback_context(query: str) -> str:
    query_lower = query.lower()
    if "ransomware" in query_lower:
        return (
            "NIST SP 800-61 Ransomware Response:\n"
            "1. Isolate affected systems immediately\n"
            "2. Identify the ransomware variant\n"
            "3. Assess backup availability\n"
            "4. Notify legal and executive team\n"
            "5. Restore from clean backups after eradication\n\n"
            "MITRE ATT&CK: T1486 - Data Encrypted for Impact\n"
            "OWASP: Focus on backup integrity and access controls"
        )
    elif "phishing" in query_lower:
        return (
            "NIST SP 800-61 Phishing Response:\n"
            "1. Quarantine malicious emails\n"
            "2. Block sender domains and IPs\n"
            "3. Search for similar emails organization-wide\n"
            "4. Educate affected users\n"
            "5. Review email gateway rules\n\n"
            "MITRE ATT&CK: T1566 - Phishing (Spearphishing variants)\n"
            "OWASP: A07 Authentication Failures, user awareness training"
        )
    else:
        return (
            "NIST SP 800-61 General Incident Response:\n"
            "Phase 1: Preparation - Establish IRT, tools, procedures\n"
            "Phase 2: Detection & Analysis - Monitor, analyze IOCs, prioritize\n"
            "Phase 3: Containment, Eradication & Recovery - Isolate, remove, restore\n"
            "Phase 4: Post-Incident - Lessons learned, improve defenses\n\n"
            "Standard escalation: Analyst -> Security Manager -> CISO\n"
            "Document all actions with timestamps for legal/compliance purposes"
        )
