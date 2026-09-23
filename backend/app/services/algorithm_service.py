"""Application-neutral adapters for executing the four Phase 3 algorithms."""

from backend.app.algorithms.astar import a_star_search
from backend.app.algorithms.bfs import breadth_first_search
from backend.app.algorithms.greedy_allocation import allocate_blood
from backend.app.algorithms.red_black_tree import RedBlackTree


def run_bfs(graph, source):
    return breadth_first_search(graph, source)


def run_greedy_allocation(required_units, inventory_candidates, blood_group=None):
    return allocate_blood(required_units, inventory_candidates, blood_group)


def run_astar(graph, source, destination, coordinates=None):
    return a_star_search(graph, source, destination, coordinates)


def prioritize_requests(requests):
    tree = RedBlackTree()
    for request in requests:
        tree.insert(request)
    return tree