import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)


class RAGEvaluator:
    @staticmethod
    def evaluate_retrieval(
        query: str, retrieved_sources: List[str], expected_sources: List[str]
    ) -> Dict[str, float]:
        """
        Evaluate RAG retrieval metrics based on retrieved vs expected sources.
        """
        if not expected_sources:
            return {"precision": 1.0, "recall": 1.0, "f1_score": 1.0, "hit_rate": 1.0}

        retrieved_set: Set[str] = set(retrieved_sources)
        expected_set: Set[str] = set(expected_sources)

        intersection = retrieved_set.intersection(expected_set)

        precision = len(intersection) / len(retrieved_set) if retrieved_set else 0.0
        recall = len(intersection) / len(expected_set) if expected_set else 0.0
        f1 = (
            (2 * precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        hit_rate = 1.0 if len(intersection) > 0 else 0.0

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "hit_rate": hit_rate,
        }

    @staticmethod
    def evaluate_relevance(scores: List[float], threshold: float = 0.5) -> float:
        """
        Calculate average relevance of the top-k chunks.
        """
        if not scores:
            return 0.0

        relevant_count = sum(1 for s in scores if s >= threshold)
        return round(relevant_count / len(scores), 4)

    @staticmethod
    def evaluate_faithfulness(generated_playbook: str, retrieved_context: str) -> float:
        """
        A heuristic-based faithfulness evaluator checking how many critical facts from
        retrieved_context are mentioned in the generated playbook.
        """
        if not retrieved_context or not generated_playbook:
            return 0.0

        # Extract keywords/terms (greater than 5 characters) from retrieved context
        import re

        context_words = set(re.findall(r"\b[a-zA-Z]{5,}\b", retrieved_context.lower()))
        if not context_words:
            return 1.0

        playbook_lower = generated_playbook.lower()
        matched = sum(1 for w in context_words if w in playbook_lower)

        return round(matched / len(context_words), 4)
