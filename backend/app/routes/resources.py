from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from backend.app import db
from backend.app.audit import record_audit
from backend.app.errors import ApiError
from backend.app.models import (
    Allocation,
    AuditLog,
    BloodInventory,
    BloodInventoryTransaction,
    BloodRequest,
    Dispatch,
    Hospital,
    HospitalConnection,
    Route,
)
from backend.app.security.jwt import auth_required, require_role
from backend.app.security.validation import require_blood_group, require_positive_id, require_positive_units, require_urgency

resources_bp = Blueprint("resources", __name__, url_prefix="/api")


def _body():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiError("Request body must be a JSON object", 400, "invalid_json")
    return payload


def hospital_json(hospital):
    return {"id": hospital.id, "code": hospital.code, "name": hospital.name, "latitude": float(hospital.latitude), "longitude": float(hospital.longitude), "address": hospital.address, "status": hospital.status, "created_at": hospital.created_at.isoformat() if hospital.created_at else None}


def inventory_json(item):
    return {"id": item.id, "hospital_id": item.hospital_id, "blood_group": item.blood_group, "units_available": item.units_available, "updated_at": item.updated_at.isoformat() if item.updated_at else None}


def request_json(item):
    return {"id": item.id, "requesting_hospital_id": item.requesting_hospital_id, "blood_group": item.blood_group, "required_units": item.required_units, "urgency": item.urgency, "notes": item.notes, "priority_score": item.priority_score, "status": item.status, "created_at": item.created_at.isoformat() if item.created_at else None}


def route_json(item):
    return {"id": item.id, "request_id": item.request_id, "source_hospital_id": item.source_hospital_id, "destination_hospital_id": item.destination_hospital_id, "path": item.path_json, "distance_km": float(item.distance_km), "estimated_minutes": item.estimated_minutes, "created_at": item.created_at.isoformat() if item.created_at else None}


def dispatch_json(item):
    return {"id": item.id, "request_id": item.request_id, "status": item.status, "dispatched_at": item.dispatched_at.isoformat() if item.dispatched_at else None, "delivered_at": item.delivered_at.isoformat() if item.delivered_at else None}


@resources_bp.get("/hospitals")
@auth_required
def hospitals():
    return jsonify({"success": True, "data": [hospital_json(item) for item in Hospital.query.order_by(Hospital.code).all()]})


@resources_bp.get("/hospitals/<int:hospital_id>")
@auth_required
def hospital_detail(hospital_id):
    hospital = db.session.get(Hospital, hospital_id)
    if hospital is None:
        raise ApiError("Hospital not found", 404, "not_found")
    connections = HospitalConnection.query.filter((HospitalConnection.source_hospital_id == hospital_id) | (HospitalConnection.destination_hospital_id == hospital_id)).all()
    inventory = BloodInventory.query.filter_by(hospital_id=hospital_id).order_by(BloodInventory.blood_group).all()
    payload = hospital_json(hospital)
    payload.update({"connections": [{"source_hospital_id": item.source_hospital_id, "destination_hospital_id": item.destination_hospital_id, "distance_km": float(item.distance_km), "estimated_minutes": item.estimated_minutes} for item in connections], "inventory": [inventory_json(item) for item in inventory]})
    return jsonify({"success": True, "data": payload})


@resources_bp.get("/inventory")
@auth_required
def inventory():
    return jsonify({"success": True, "data": [inventory_json(item) for item in BloodInventory.query.order_by(BloodInventory.hospital_id, BloodInventory.blood_group).all()]})


@resources_bp.get("/inventory/<int:hospital_id>")
@auth_required
def hospital_inventory(hospital_id):
    if db.session.get(Hospital, hospital_id) is None:
        raise ApiError("Hospital not found", 404, "not_found")
    return jsonify({"success": True, "data": [inventory_json(item) for item in BloodInventory.query.filter_by(hospital_id=hospital_id).order_by(BloodInventory.blood_group).all()]})


@resources_bp.put("/inventory/<int:inventory_id>")
@require_role("ADMIN", "HOSPITAL", "INVENTORY_MANAGER")
def update_inventory(inventory_id):
    item = db.session.get(BloodInventory, inventory_id)
    if item is None:
        raise ApiError("Inventory record not found", 404, "not_found")
    payload = _body()
    units = payload.get("units_available")
    try:
        units = require_positive_units(units) if units != 0 else 0
    except ValueError as exc:
        raise ApiError(str(exc), 422, "validation_error") from exc
    item.units_available = units
    record_audit("INVENTORY_UPDATE", "blood_inventory", item.id, {"hospital_id": item.hospital_id, "units_available": units})
    db.session.commit()
    return jsonify({"success": True, "data": inventory_json(item)})


@resources_bp.get("/requests")
@auth_required
def requests():
    return jsonify({"success": True, "data": [request_json(item) for item in BloodRequest.query.order_by(BloodRequest.created_at.desc()).all()]})


@resources_bp.post("/requests")
@auth_required
def create_request():
    payload = _body()
    try:
        hospital_id = require_positive_id(payload.get("requesting_hospital_id", payload.get("destination_hospital_id")), "hospital_id")
        blood_group = require_blood_group(payload.get("blood_group"))
        units = require_positive_units(payload.get("required_units"))
        urgency = require_urgency(payload.get("urgency"))
    except ValueError as exc:
        raise ApiError(str(exc), 422, "validation_error") from exc
    if db.session.get(Hospital, hospital_id) is None:
        raise ApiError("Hospital not found", 404, "not_found")
    priority_scores = {"CRITICAL": 100, "HIGH": 75, "MEDIUM": 50, "NORMAL": 25}
    notes = payload.get("notes")
    if notes is not None and (not isinstance(notes, str) or len(notes) > 2000):
        raise ApiError("Notes must be text of 2000 characters or fewer", 422, "validation_error")
    item = BloodRequest(requesting_hospital_id=hospital_id, blood_group=blood_group, required_units=units, urgency=urgency, notes=notes.strip() if isinstance(notes, str) else None, priority_score=priority_scores[urgency])
    db.session.add(item)
    db.session.flush()
    record_audit("CREATE_REQUEST", "blood_request", item.id, {"blood_group": blood_group, "required_units": units, "urgency": urgency})
    db.session.commit()
    return jsonify({"success": True, "data": request_json(item)}), 201


@resources_bp.get("/requests/<int:request_id>")
@auth_required
def request_detail(request_id):
    item = db.session.get(BloodRequest, request_id)
    if item is None:
        raise ApiError("Request not found", 404, "not_found")
    payload = request_json(item)
    payload["allocations"] = [{"id": row.id, "hospital_id": row.hospital_id, "units_allocated": row.units_allocated, "created_at": row.created_at.isoformat() if row.created_at else None} for row in Allocation.query.filter_by(request_id=request_id).all()]
    payload["routes"] = [route_json(row) for row in Route.query.filter_by(request_id=request_id).all()]
    payload["dispatches"] = [dispatch_json(row) for row in Dispatch.query.filter_by(request_id=request_id).all()]
    return jsonify({"success": True, "data": payload})


@resources_bp.put("/requests/<int:request_id>/status")
@require_role("ADMIN", "HOSPITAL", "DISPATCHER")
def update_request_status(request_id):
    item = db.session.get(BloodRequest, request_id)
    if item is None:
        raise ApiError("Request not found", 404, "not_found")
    status = (_body().get("status") or "").upper()
    allowed = {"PENDING", "PROCESSING", "PARTIALLY_ALLOCATED", "FULFILLED", "DISPATCHED", "FAILED"}
    if status not in allowed:
        raise ApiError("Invalid request status", 422, "validation_error")
    item.status = status
    record_audit("UPDATE_REQUEST_STATUS", "blood_request", item.id, {"status": status})
    db.session.commit()
    return jsonify({"success": True, "data": request_json(item)})


@resources_bp.get("/routes")
@auth_required
def routes():
    return jsonify({"success": True, "data": [route_json(item) for item in Route.query.order_by(Route.created_at.desc()).all()]})


@resources_bp.get("/routes/<int:request_id>")
@auth_required
def request_routes(request_id):
    return jsonify({"success": True, "data": [route_json(item) for item in Route.query.filter_by(request_id=request_id).all()]})


@resources_bp.get("/allocations/<int:request_id>")
@auth_required
def allocations(request_id):
    return jsonify({"success": True, "data": [{"id": item.id, "request_id": item.request_id, "hospital_id": item.hospital_id, "units_allocated": item.units_allocated, "created_at": item.created_at.isoformat() if item.created_at else None} for item in Allocation.query.filter_by(request_id=request_id).all()]})


@resources_bp.get("/dispatch")
@auth_required
def dispatches():
    return jsonify({"success": True, "data": [dispatch_json(item) for item in Dispatch.query.order_by(Dispatch.id.desc()).all()]})


@resources_bp.post("/dispatch")
@require_role("ADMIN", "DISPATCHER")
def create_dispatch():
    payload = _body()
    try:
        request_id = require_positive_id(payload.get("request_id"), "request_id")
    except ValueError as exc:
        raise ApiError(str(exc), 422, "validation_error") from exc
    if db.session.get(BloodRequest, request_id) is None:
        raise ApiError("Request not found", 404, "not_found")
    item = Dispatch(request_id=request_id, status="CREATED")
    db.session.add(item)
    db.session.flush()
    record_audit("DISPATCH_CREATED", "dispatch", item.id)
    db.session.commit()
    return jsonify({"success": True, "data": dispatch_json(item)}), 201


@resources_bp.get("/audit-logs")
@require_role("ADMIN")
def audit_logs():
    rows = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return jsonify({"success": True, "data": [{"id": item.id, "user_id": item.user_id, "action": item.action, "entity": item.entity, "entity_id": item.entity_id, "ip_address": item.ip_address, "metadata": item.metadata_json, "created_at": item.created_at.isoformat() if item.created_at else None} for item in rows]})


@resources_bp.get("/analytics/dashboard")
@auth_required
def dashboard_analytics():
    all_requests = BloodRequest.query.all()
    return jsonify({"success": True, "data": {"total_requests": len(all_requests), "urgent_requests": sum(item.urgency in {"CRITICAL", "HIGH"} for item in all_requests), "connected_hospitals": Hospital.query.filter_by(status="ACTIVE").count(), "available_units": sum(item.units_available for item in BloodInventory.query.all())}})
