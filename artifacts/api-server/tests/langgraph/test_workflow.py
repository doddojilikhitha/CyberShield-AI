from graph.workflow import build_workflow, route_after_review


def test_workflow_conditional_routing():
    # Test route_after_review routing rules
    state_approved = {"review_status": "approved", "reviewer_feedback": None}
    assert route_after_review(state_approved) == "end"

    state_rejected = {
        "review_status": "rejected",
        "reviewer_feedback": "Please add ransomware procedures",
    }
    assert route_after_review(state_rejected) == "regenerate"


def test_workflow_structure():
    graph = build_workflow()
    assert graph is not None

    # Check nodes exist
    node_names = [node for node in graph.nodes.keys()]
    assert "classify" in node_names
    assert "map_frameworks" in node_names
    assert "retrieve_rag" in node_names
    assert "generate_playbook" in node_names
    assert "review_compliance" in node_names
    assert "regenerate_playbook" in node_names
