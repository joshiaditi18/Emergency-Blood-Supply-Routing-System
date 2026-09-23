"""Manual A* pathfinding over weighted hospital graph edges.

Edges may be ``(neighbor, distance, estimated_minutes)`` tuples or mappings
with ``node``/``neighbor``, ``distance`` and ``estimated_minutes`` fields.
The distance is the route cost; estimated travel time is returned separately.
"""

from heapq import heappop, heappush
from math import asin, cos, radians, sin, sqrt


def haversine_distance(first, second):
    """Return geographic distance in kilometres between ``(lat, lon)`` pairs."""
    lat1, lon1 = first
    lat2, lon2 = second
    earth_radius_km = 6371.0
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    value = sin(delta_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(delta_lon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(value))


def _edge_values(edge):
    if isinstance(edge, dict):
        neighbor = edge.get("neighbor", edge.get("node"))
        return neighbor, float(edge.get("distance", edge.get("cost", 1))), int(edge.get("estimated_minutes", 0))
    if len(edge) == 2:
        return edge[0], float(edge[1]), 0
    return edge[0], float(edge[1]), int(edge[2])


def _heuristic(node, destination, coordinates):
    if coordinates and node in coordinates and destination in coordinates:
        return haversine_distance(coordinates[node], coordinates[destination])
    return 0.0


def a_star_search(graph, source, destination, coordinates=None):
    """Find a lowest-distance path and expose actual A* score bookkeeping."""
    if source not in graph or destination not in graph:
        raise ValueError("source and destination must exist in graph")
    coordinates = coordinates or {}
    open_set = []
    heappush(open_set, (_heuristic(source, destination, coordinates), source))
    came_from = {}
    g_values = {source: 0.0}
    h_values = {source: _heuristic(source, destination, coordinates)}
    f_values = {source: h_values[source]}
    travel_times = {source: 0}
    expanded_nodes = []
    closed = set()

    while open_set:
        _, current = heappop(open_set)
        if current in closed:
            continue
        closed.add(current)
        expanded_nodes.append(current)
        if current == destination:
            path = [current]
            while path[-1] != source:
                path.append(came_from[path[-1]])
            path.reverse()
            return {
                "source": source,
                "destination": destination,
                "path": path,
                "total_cost": g_values[destination],
                "distance": g_values[destination],
                "estimated_time": travel_times[destination],
                "expanded_nodes": expanded_nodes,
                "nodes_explored": expanded_nodes,
                "g_values": g_values,
                "h_values": h_values,
                "f_values": f_values,
            }
        for raw_edge in graph.get(current, ()):
            neighbor, distance, minutes = _edge_values(raw_edge)
            if neighbor in closed:
                continue
            tentative_g = g_values[current] + distance
            if tentative_g < g_values.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_values[neighbor] = tentative_g
                travel_times[neighbor] = travel_times[current] + minutes
                h_values[neighbor] = _heuristic(neighbor, destination, coordinates)
                f_values[neighbor] = tentative_g + h_values[neighbor]
                heappush(open_set, (f_values[neighbor], neighbor))

    return {
        "source": source,
        "destination": destination,
        "path": [],
        "total_cost": None,
        "distance": None,
        "estimated_time": None,
        "expanded_nodes": expanded_nodes,
        "nodes_explored": expanded_nodes,
        "g_values": g_values,
        "h_values": h_values,
        "f_values": f_values,
    }
