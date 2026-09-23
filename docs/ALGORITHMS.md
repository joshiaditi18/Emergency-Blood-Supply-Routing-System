# Phase 3 Algorithms

Phase 3 implements the four core algorithms manually. They are exposed through `backend/app/services/algorithm_service.py`; no frontend or HTTP algorithm endpoints are added yet.

## BFS

`breadth_first_search(graph, source)` uses a list-backed FIFO queue with a moving index, a visited set, and a level map. It returns traversal order, visited nodes, BFS levels, and candidate hospitals.

- Time: O(V + E)
- Auxiliary space: O(V)

The graph is an adjacency mapping of hospital IDs to connected hospital IDs.

## Red-Black Tree

`RedBlackTree` uses an explicit black sentinel leaf. It implements insertion, deletion, left/right rotations, recoloring, insertion fix-up, deletion fix-up, exact-key search, and highest-priority lookup.

Priority keys are `(urgency_rank, created_timestamp, request_id)`, so higher urgency wins, newer requests break urgency ties, and request ID guarantees uniqueness.

- Insert: O(log n)
- Search: O(log n)
- Delete: O(log n)
- Highest priority: O(log n)
- Auxiliary space: O(n)

The implementation maintains a black root, no red-red parent/child pair, equal black height, and BST ordering.

## Greedy Blood Allocation

`allocate_blood()` repeatedly scans remaining eligible inventory and selects the hospital with the maximum currently available compatible units. It can take a partial amount from the selected hospital and continues until the request is fulfilled or candidates are exhausted.

- Time: O(H^2) for H candidate hospitals
- Auxiliary space: O(H)

Returned data includes required, allocated, and remaining units, selected hospitals, per-hospital allocations, allocation steps, and `COMPLETED`/`FAILED` status.

## A*

`a_star_search()` uses a manually managed open-set heap and explicit `g`, `h`, and `f` maps. Edge distance is the optimization cost; estimated travel minutes are accumulated separately and are not inferred as traffic-aware live time. Optional coordinates enable a Haversine geographic heuristic.

- With a binary heap: O((V + E) log V) worst-case
- Auxiliary space: O(V)

The result includes path, total distance/cost, estimated travel time, expanded nodes, and score maps. Disconnected destinations return an empty path and `None` cost/time.
