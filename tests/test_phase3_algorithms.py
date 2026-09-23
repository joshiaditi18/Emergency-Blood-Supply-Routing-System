from datetime import datetime, timedelta, timezone

import pytest

from backend.app.algorithms.astar import a_star_search
from backend.app.algorithms.bfs import breadth_first_search
from backend.app.algorithms.greedy_allocation import allocate_blood
from backend.app.algorithms.red_black_tree import BLACK, RED, PriorityRecord, RedBlackTree
from backend.app.services.algorithm_service import prioritize_requests, run_bfs, run_greedy_allocation


def test_bfs_returns_order_levels_and_candidates():
    graph = {"H1": ["H2", "H3"], "H2": ["H4"], "H3": ["H4"], "H4": []}
    result = breadth_first_search(graph, "H1")
    assert result["traversal_order"] == ["H1", "H2", "H3", "H4"]
    assert result["levels"] == {"H1": 0, "H2": 1, "H3": 1, "H4": 2}
    assert result["candidate_hospitals"] == ["H2", "H3", "H4"]
    assert result["visited"] == set(graph)


def test_bfs_rejects_unknown_source():
    with pytest.raises(ValueError):
        breadth_first_search({"H1": []}, "H9")


def test_red_black_tree_priority_and_bst_invariants():
    now = datetime.now(timezone.utc)
    tree = RedBlackTree()
    records = [
        PriorityRecord(1, "NORMAL", now),
        PriorityRecord(2, "CRITICAL", now - timedelta(minutes=5)),
        PriorityRecord(3, "CRITICAL", now),
        PriorityRecord(4, "HIGH", now),
    ]
    for record in records:
        tree.insert(record)
    assert tree.root.color == BLACK
    assert tree.get_highest_priority().request_id == 3

    def inspect(node):
        if node == tree.nil:
            return 1, []
        assert node.color in {RED, BLACK}
        if node.color == RED:
            assert node.left.color == BLACK
            assert node.right.color == BLACK
        left_height, left_keys = inspect(node.left)
        right_height, right_keys = inspect(node.right)
        assert left_height == right_height
        assert all(key < node.key for key in left_keys)
        assert all(key > node.key for key in right_keys)
        return left_height + (1 if node.color == BLACK else 0), left_keys + [node.key] + right_keys

    _, keys = inspect(tree.root)
    assert keys == sorted(keys)


def test_red_black_tree_delete_preserves_invariants():
    now = datetime.now(timezone.utc)
    tree = RedBlackTree()
    records = [PriorityRecord(index, "HIGH", now + timedelta(seconds=index)) for index in range(1, 15)]
    for record in records:
        tree.insert(record)
    for record in records[::2]:
        tree.delete(tree.priority_key(record)[:3])
    assert tree.root == tree.nil or tree.root.color == BLACK
    assert tree.search(tree.priority_key(records[0])[:3]) is None
    assert tree.get_highest_priority().request_id == 14


def test_greedy_sufficient_exact_and_multi_hospital_allocation():
    candidates = [
        {"hospital_id": "A", "blood_group": "O+", "units_available": 4},
        {"hospital_id": "B", "blood_group": "O+", "units_available": 3},
        {"hospital_id": "C", "blood_group": "O+", "units_available": 2},
    ]
    result = allocate_blood(6, candidates, "O+")
    assert result["status"] == "COMPLETED"
    assert result["allocated_units"] == 6
    assert result["remaining_units"] == 0
    assert result["allocations"] == [{"hospital_id": "A", "units_taken": 4}, {"hospital_id": "B", "units_taken": 2}]


def test_greedy_insufficient_returns_partial_without_overallocation():
    result = allocate_blood(10, [{"hospital_id": "A", "units_available": 4}, {"hospital_id": "B", "units_available": 3}])
    assert result["status"] == "FAILED"
    assert result["allocated_units"] == 7
    assert result["remaining_units"] == 3


def test_greedy_filters_incompatible_inventory():
    result = allocate_blood(5, [{"hospital_id": "A", "blood_group": "A+", "units_available": 20}], "O-")
    assert result["allocated_units"] == 0
    assert result["remaining_units"] == 5


def test_astar_returns_shortest_path_and_score_bookkeeping():
    graph = {
        "H1": [("H2", 4, 8), ("H3", 2, 5)],
        "H2": [("H4", 3, 6)],
        "H3": [("H4", 8, 12)],
        "H4": [],
    }
    result = a_star_search(graph, "H1", "H4")
    assert result["path"] == ["H1", "H2", "H4"]
    assert result["distance"] == 7
    assert result["estimated_time"] == 14
    assert result["f_values"]["H2"] == result["g_values"]["H2"] + result["h_values"]["H2"]
    assert "H4" in result["expanded_nodes"]


def test_astar_reports_disconnected_destination():
    result = a_star_search({"H1": [], "H2": []}, "H1", "H2")
    assert result["path"] == []
    assert result["total_cost"] is None


def test_algorithm_service_executes_real_algorithms():
    bfs_result = run_bfs({"H1": ["H2"], "H2": []}, "H1")
    allocation_result = run_greedy_allocation(1, [{"hospital_id": 1, "units_available": 1}])
    tree = prioritize_requests([PriorityRecord(1, "CRITICAL", datetime.now(timezone.utc))])
    assert bfs_result["traversal_order"] == ["H1", "H2"]
    assert allocation_result["allocated_units"] == 1
    assert tree.get_highest_priority().request_id == 1