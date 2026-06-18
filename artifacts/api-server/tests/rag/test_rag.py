from rag.evaluation import RAGEvaluator


def test_retrieval_metrics():
    retrieved = ["nist_guide.txt", "mitre_attack.txt"]
    expected = ["nist_guide.txt", "mitre_attack.txt", "owasp_guide.txt"]

    metrics = RAGEvaluator.evaluate_retrieval(
        query="phishing investigation",
        retrieved_sources=retrieved,
        expected_sources=expected,
    )

    assert metrics["precision"] == 1.0  # All retrieved are expected
    assert metrics["recall"] == round(2 / 3, 4)  # 2 out of 3 expected retrieved
    assert metrics["hit_rate"] == 1.0  # At least one match


def test_relevance_evaluator():
    scores = [0.8, 0.6, 0.4, 0.2]
    # Hits at or above threshold 0.5
    avg_relevance = RAGEvaluator.evaluate_relevance(scores, threshold=0.5)
    assert avg_relevance == 0.5  # 2 out of 4 are >= 0.5


def test_faithfulness_evaluator():
    context = "Containment requires isolating the server and blocking port 8080."
    playbook = (
        "Containment steps: Isolating the server and blocking port 8080 immediately."
    )

    score = RAGEvaluator.evaluate_faithfulness(playbook, context)
    assert score > 0.5  # High match on terms
