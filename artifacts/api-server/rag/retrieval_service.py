import logging
from typing import List, Tuple, Optional
from rag.embedding_service import OpenAIEmbeddingService
from rag.chroma_service import ChromaService

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(
        self, chroma_service: ChromaService, embedding_service: OpenAIEmbeddingService
    ):
        self.chroma = chroma_service
        self.embedding = embedding_service

    def retrieve_context(
        self, query: str, k: int = 5, where: Optional[dict] = None
    ) -> Tuple[str, List[str], List[float]]:
        """
        Retrieves context chunks from ChromaDB for the given query.
        Returns:
            Tuple containing:
            1. Formatted context string.
            2. List of source document names.
            3. Similarity scores (relevance scores) for each retrieved chunk.
        """
        try:
            # 1. Generate query embedding
            query_embedding = self.embedding.get_embedding(query)

            # 2. Query ChromaDB collection
            results = self.chroma.query(query_embedding, n_results=k, where=where)

            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            if not documents:
                return "No matching security guidance found in database.", [], []

            context_parts = []
            sources = []
            scores = []

            for i, doc in enumerate(documents):
                meta = metadatas[i] if i < len(metadatas) else {}
                source = meta.get("source", "unknown")
                dist = distances[i] if i < len(distances) else 0.0

                # Cosine distance is returned. Cosine similarity = 1.0 - distance
                similarity = 1.0 - dist
                scores.append(similarity)

                context_parts.append(
                    f"[Source: {source}] (Relevance Score: {similarity:.2f})\n{doc}"
                )
                if source not in sources:
                    sources.append(source)

            context_str = "\n\n---\n\n".join(context_parts)
            return context_str, sources, scores

        except Exception as e:
            logger.error(f"Error retrieving context for query '{query}': {e}")
            return (
                "Fallback: Retrieve basic NIST SP 800-61 incident response standard guidance.",
                ["Fallback Guidance"],
                [0.0],
            )
