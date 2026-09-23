"""Manual breadth-first search for hospital connection graphs.

Complexity is O(V + E) time and O(V) auxiliary space.
"""


def breadth_first_search(graph, source):
    """Traverse ``graph`` from ``source`` using a manually managed queue.

    ``graph`` is an adjacency mapping whose values are iterables of node IDs.
    The source is included in traversal order and candidate hospitals contain
    every discovered node except the source.
    """
    if source not in graph:
        raise ValueError("source must exist in graph")

    queue = [source]
    queue_index = 0
    visited = {source}
    traversal_order = []
    levels = {source: 0}

    while queue_index < len(queue):
        current = queue[queue_index]
        queue_index += 1
        traversal_order.append(current)
        for neighbor in graph.get(current, ()):
            if neighbor not in visited:
                visited.add(neighbor)
                levels[neighbor] = levels[current] + 1
                queue.append(neighbor)

    return {
        "source": source,
        "traversal_order": traversal_order,
        "visited": visited,
        "levels": levels,
        "candidate_hospitals": traversal_order[1:],
    }
