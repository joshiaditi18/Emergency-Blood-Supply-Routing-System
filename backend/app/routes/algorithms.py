from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from backend.app import db
from backend.app.algorithms.red_black_tree import PriorityRecord, RedBlackTree
from backend.app.audit import record_audit
from backend.app.errors import ApiError
from backend.app.models import Allocation, BloodInventory, BloodInventoryTransaction, BloodRequest, Dispatch, Hospital, HospitalConnection, Route
from backend.app.security.jwt import auth_required, require_role
from backend.app.security.validation import require_blood_group, require_positive_id, require_positive_units
from backend.app.services.algorithm_service import run_astar, run_bfs, run_greedy_allocation
from backend.app.utils.blood_compatibility import compatible_donor_groups

algorithms_bp = Blueprint("algorithms", __name__, url_prefix="/api/algorithms")


def _body():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiError("Request body must be a JSON object", 400, "invalid_json")
    return payload


def _graph_data():
    connections = HospitalConnection.query.filter_by(is_active=True).all()
    hospitals = Hospital.query.all()
    graph = {item.id: [] for item in hospitals}
    weighted = {item.id: [] for item in hospitals}
    coordinates = {item.id: (float(item.latitude), float(item.longitude)) for item in hospitals}
    for connection in connections:
        graph[connection.source_hospital_id].append(connection.destination_hospital_id)
        weighted[connection.source_hospital_id].append((connection.destination_hospital_id, float(connection.distance_km), connection.estimated_minutes))
    return graph, weighted, coordinates


def _tree_snapshot(tree):
    def visit(node):
        if node == tree.nil:
            return None
        return {"key": list(node.key), "request_id": node.item.request_id, "urgency": node.item.urgency, "created_at": node.item.created_at.isoformat(), "color": node.color, "left": visit(node.left), "right": visit(node.right)}
    return visit(tree.root)


@algorithms_bp.post("/bfs")
@auth_required
def bfs_endpoint():
    payload = _body()
    try:
        source = require_positive_id(payload.get("source_hospital_id", payload.get("source")), "source_hospital_id")
    except ValueError as exc:
        raise ApiError(str(exc), 422, "validation_error") from exc
    graph, _, _ = _graph_data()
    try:
        result = run_bfs(graph, source)
    except ValueError as exc:
        raise ApiError(str(exc), 404, "not_found") from exc
    record_audit("ALGORITHM_BFS", "hospital", source)
    db.session.commit()
    return jsonify({"success": True, "data": {**result, "visited": list(result["visited"]), "graph": graph}})


@algorithms_bp.post("/greedy")
@auth_required
def greedy_endpoint():
    payload = _body()
    try:
        blood_group = require_blood_group(payload.get("blood_group"))
        required_units = require_positive_units(payload.get("required_units"))
    except ValueError as exc:
        raise ApiError(str(exc), 422, "validation_error") from exc
    hospital_ids = payload.get("hospital_ids")
    query = BloodInventory.query.filter(BloodInventory.blood_group.in_(compatible_donor_groups(blood_group)), BloodInventory.units_available > 0)
    if isinstance(hospital_ids, list) and hospital_ids:
        try:
            hospital_ids = [require_positive_id(value, "hospital_id") for value in hospital_ids]
        except ValueError as exc:
            raise ApiError(str(exc), 422, "validation_error") from exc
        query = query.filter(BloodInventory.hospital_id.in_(hospital_ids))
    result = run_greedy_allocation(required_units, query.all(), blood_group)
    result["blood_group"] = blood_group
    record_audit("ALGORITHM_GREEDY", "blood_inventory", metadata={"blood_group": blood_group, "required_units": required_units})
    db.session.commit()
    return jsonify({"success": True, "data": result})


@algorithms_bp.post("/astar")
@auth_required
def astar_endpoint():
    payload = _body()
    try:
        source = require_positive_id(payload.get("source_hospital_id", payload.get("source")), "source_hospital_id")
        destination = require_positive_id(payload.get("destination_hospital_id", payload.get("destination")), "destination_hospital_id")
    except ValueError as exc:
        raise ApiError(str(exc), 422, "validation_error") from exc
    _, weighted, coordinates = _graph_data()
    try:
        result = run_astar(weighted, source, destination, coordinates)
    except ValueError as exc:
        raise ApiError(str(exc), 404, "not_found") from exc
    record_audit("ALGORITHM_ASTAR", "hospital", destination)
    db.session.commit()
    return jsonify({"success": True, "data": result})


@algorithms_bp.post("/priority")
@auth_required
def priority_endpoint():
    requests = BloodRequest.query.filter(BloodRequest.status.in_(["PENDING", "PROCESSING"])).all()
    tree = RedBlackTree()
    for item in requests:
        tree.insert(PriorityRecord(item.id, item.urgency, item.created_at, item.priority_score))
    return jsonify({"success": True, "data": {"highest_priority": tree.get_highest_priority().request_id if tree.get_highest_priority() else None, "tree": _tree_snapshot(tree)}})


@algorithms_bp.post("/process-request")
@require_role("ADMIN", "HOSPITAL", "DISPATCHER", "USER")
def process_request():
    payload = _body()
    try:
        request_id = require_positive_id(payload.get("request_id"), "request_id")
    except ValueError as exc:
        raise ApiError(str(exc), 422, "validation_error") from exc
    request_item = db.session.get(BloodRequest, request_id)
    if request_item is None:
        raise ApiError("Request not found", 404, "not_found")
    if request_item.status not in {"PENDING", "PROCESSING"}:
        raise ApiError("Request has already been processed", 409, "request_already_processed")
    request_item.status = "PROCESSING"
    graph, weighted, coordinates = _graph_data()
    priority_tree = RedBlackTree()
    pending_requests = BloodRequest.query.filter(BloodRequest.status.in_(["PENDING", "PROCESSING"])).all()
    for item in pending_requests:
        priority_tree.insert(PriorityRecord(item.id, item.urgency, item.created_at, item.priority_score))
    bfs_result = run_bfs(graph, request_item.requesting_hospital_id)
    candidate_ids = bfs_result["candidate_hospitals"]
    donor_rows = BloodInventory.query.filter(
        BloodInventory.hospital_id.in_(candidate_ids),
        BloodInventory.blood_group.in_(compatible_donor_groups(request_item.blood_group)),
        BloodInventory.units_available > 0,
    ).with_for_update().all()
    eligible_inventory = [{"hospital_id": row.hospital_id, "blood_group": row.blood_group, "units_available": row.units_available} for row in donor_rows]
    allocation_result = run_greedy_allocation(request_item.required_units, donor_rows, request_item.blood_group)
    allocation_result["compatible_donor_groups"] = sorted(compatible_donor_groups(request_item.blood_group))
    allocation_result["eligible_inventory"] = eligible_inventory
    if allocation_result["status"] != "COMPLETED":
        request_item.status = "FAILED"
        record_audit("ALLOCATE_BLOOD", "blood_request", request_id, {"status": "INSUFFICIENT_INVENTORY"})
        db.session.commit()
        raise ApiError("Insufficient compatible inventory", 409, "insufficient_inventory", {"compatible_donor_groups": sorted(compatible_donor_groups(request_item.blood_group)), "eligible_inventory": eligible_inventory, "allocation": allocation_result})
    route_results = []
    for allocation in allocation_result["allocations"]:
        route = run_astar(weighted, allocation["hospital_id"], request_item.requesting_hospital_id, coordinates)
        route_results.append({"inventory_id": allocation["inventory_id"], "hospital_id": allocation["hospital_id"], "route": route})
    if any(not item["route"]["path"] for item in route_results):
        db.session.rollback()
        raise ApiError("No route found for allocation", 409, "no_route")
    for allocation in allocation_result["allocations"]:
        inventory_row = next(row for row in donor_rows if row.id == allocation["inventory_id"])
        if inventory_row.units_available < allocation["units_taken"]:
            db.session.rollback()
            raise ApiError("Inventory changed while processing this request", 409, "concurrent_allocation")
    route_records = []
    dispatch_records = []
    for allocation in allocation_result["allocations"]:
        inventory_row = next(row for row in donor_rows if row.id == allocation["inventory_id"])
        units = allocation["units_taken"]
        inventory_row.units_available -= units
        db.session.add(BloodInventoryTransaction(inventory_id=inventory_row.id, request_id=request_id, change_units=-units, reason="EMERGENCY_ALLOCATION"))
        db.session.add(Allocation(request_id=request_id, hospital_id=inventory_row.hospital_id, units_allocated=units))
        route = next(item["route"] for item in route_results if item["inventory_id"] == allocation["inventory_id"])
        route_record = Route(request_id=request_id, source_hospital_id=route["path"][0], destination_hospital_id=route["path"][-1], path_json=route["path"], distance_km=route["distance"], estimated_minutes=route["estimated_time"])
        dispatch = Dispatch(request_id=request_id, status="CREATED")
        db.session.add(route_record)
        db.session.add(dispatch)
        route_records.append(route_record)
        dispatch_records.append(dispatch)
    request_item.status = "FULFILLED"
    record_audit("ALLOCATE_BLOOD", "blood_request", request_id, {"allocated_units": allocation_result["allocated_units"]})
    record_audit("ROUTE_CALCULATED", "blood_request", request_id, {"route_count": len(route_records)})
    record_audit("DISPATCH_CREATED", "blood_request", request_id)
    db.session.commit()
    return jsonify({"success": True, "data": {"request": {"id": request_item.id, "status": request_item.status}, "priority": {"highest_priority": priority_tree.get_highest_priority().request_id if priority_tree.get_highest_priority() else None, "tree": _tree_snapshot(priority_tree)}, "bfs": {**bfs_result, "visited": list(bfs_result["visited"])}, "allocation": allocation_result, "routes": [{"hospital_id": item["hospital_id"], **item["route"]} for item in route_results], "route": route_results[0]["route"], "dispatch": {"id": dispatch_records[0].id, "status": dispatch_records[0].status}, "dispatches": [{"id": item.id, "status": item.status} for item in dispatch_records], "status": request_item.status}})
