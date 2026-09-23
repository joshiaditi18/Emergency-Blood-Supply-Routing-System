from datetime import datetime, timezone

import pytest

from backend.app import create_app, db
from backend.app.models import BloodInventory, Hospital, HospitalConnection, User
from backend.app.security.passwords import hash_password


class ApiConfig:
    TESTING = True
    SECRET_KEY = "phase4-test-secret"
    JWT_SECRET_KEY = "phase4-access-secret"
    JWT_REFRESH_SECRET_KEY = "phase4-refresh-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ["http://127.0.0.1:5173"]
    JWT_ACCESS_EXPIRES_SECONDS = 900
    JWT_REFRESH_EXPIRES_SECONDS = 604800
    RATE_LIMIT_WINDOW_SECONDS = 60
    RATE_LIMIT_LOGIN = 20
    RATE_LIMIT_REGISTER = 20
    RATE_LIMIT_REFRESH = 20


@pytest.fixture()
def client():
    app = create_app(ApiConfig)
    with app.app_context():
        db.create_all()
        db.session.add(User(email="admin@phase4.test", password_hash=hash_password("AdminPassword!123"), role="ADMIN", full_name="Phase Four Admin"))
        hospitals = [Hospital(code=f"H{index}", name=f"Hospital {index}", latitude=28.6 + index / 100, longitude=77.2 + index / 100) for index in range(1, 4)]
        db.session.add_all(hospitals)
        db.session.flush()
        db.session.add_all([
            HospitalConnection(source_hospital_id=1, destination_hospital_id=2, distance_km=4, estimated_minutes=8),
            HospitalConnection(source_hospital_id=2, destination_hospital_id=1, distance_km=4, estimated_minutes=8),
            HospitalConnection(source_hospital_id=2, destination_hospital_id=3, distance_km=5, estimated_minutes=10),
            HospitalConnection(source_hospital_id=3, destination_hospital_id=2, distance_km=5, estimated_minutes=10),
        ])
        db.session.add_all([
            BloodInventory(hospital_id=2, blood_group="O+", units_available=8),
            BloodInventory(hospital_id=2, blood_group="O-", units_available=8),
            BloodInventory(hospital_id=2, blood_group="A-", units_available=8),
            BloodInventory(hospital_id=2, blood_group="AB-", units_available=8),
            BloodInventory(hospital_id=3, blood_group="O+", units_available=4),
        ])
        db.session.commit()
    yield app.test_client()
    with app.app_context():
        db.session.remove()
        db.drop_all()


def auth_headers(client):
    response = client.post("/api/auth/login", json={"email": "admin@phase4.test", "password": "AdminPassword!123"})
    return {"Authorization": f"Bearer {response.get_json()['access_token']}"}


def test_resource_endpoints_and_algorithm_endpoints(client):
    headers = auth_headers(client)
    assert client.get("/api/hospitals", headers=headers).status_code == 200
    assert client.get("/api/inventory", headers=headers).status_code == 200
    assert client.post("/api/algorithms/bfs", headers=headers, json={"source_hospital_id": 1}).status_code == 200
    assert client.post("/api/algorithms/greedy", headers=headers, json={"blood_group": "O+", "required_units": 6}).status_code == 200
    assert client.post("/api/algorithms/astar", headers=headers, json={"source_hospital_id": 2, "destination_hospital_id": 1}).status_code == 200


def test_process_request_persists_all_workflow_records(client):
    headers = auth_headers(client)
    created = client.post("/api/requests", headers=headers, json={"requesting_hospital_id": 1, "blood_group": "O+", "required_units": 6, "urgency": "CRITICAL"})
    assert created.status_code == 201
    request_id = created.get_json()["data"]["id"]
    processed = client.post("/api/algorithms/process-request", headers=headers, json={"request_id": request_id})
    assert processed.status_code == 200, processed.get_json()
    body = processed.get_json()["data"]
    assert body["status"] == "FULFILLED"
    assert body["bfs"]["traversal_order"]
    assert body["allocation"]["allocated_units"] == 6
    assert body["route"]["path"]
    assert body["dispatch"]["id"]
    detail = client.get(f"/api/requests/{request_id}", headers=headers)
    assert detail.get_json()["data"]["allocations"]
    assert detail.get_json()["data"]["routes"]
    assert detail.get_json()["data"]["dispatches"]


def test_protected_resource_endpoint_rejects_missing_auth(client):
    response = client.get("/api/hospitals")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_process_request_uses_compatible_o_negative_inventory(client):
    headers = auth_headers(client)
    inventory = client.get("/api/inventory", headers=headers).get_json()["data"]
    o_positive = next(item for item in inventory if item["hospital_id"] == 2 and item["blood_group"] == "O+")
    assert client.put(f"/api/inventory/{o_positive['id']}", headers=headers, json={"units_available": 0}).status_code == 200
    created = client.post("/api/requests", headers=headers, json={"requesting_hospital_id": 1, "blood_group": "O+", "required_units": 6, "urgency": "CRITICAL"})
    processed = client.post("/api/algorithms/process-request", headers=headers, json={"request_id": created.get_json()["data"]["id"]})
    assert processed.status_code == 200, processed.get_json()
    allocation = processed.get_json()["data"]["allocation"]
    assert allocation["status"] == "COMPLETED"
    assert allocation["compatible_donor_groups"] == ["O+", "O-"]
    assert any(step["hospital_id"] == 2 for step in allocation["allocation_steps"])


def test_process_request_persists_one_route_and_dispatch_per_donor(client):
    headers = auth_headers(client)
    created = client.post("/api/requests", headers=headers, json={"requesting_hospital_id": 1, "blood_group": "O+", "required_units": 10, "urgency": "HIGH"})
    request_id = created.get_json()["data"]["id"]
    processed = client.post("/api/algorithms/process-request", headers=headers, json={"request_id": request_id})
    assert processed.status_code == 200
    body = processed.get_json()["data"]
    assert body["allocation"]["allocated_units"] == 10
    assert len(body["routes"]) == len(body["allocation"]["allocations"])
    detail = client.get(f"/api/requests/{request_id}", headers=headers).get_json()["data"]
    assert len(detail["routes"]) == len(detail["allocations"]) == len(detail["dispatches"])


def test_process_request_does_not_fulfill_insufficient_inventory(client):
    headers = auth_headers(client)
    created = client.post("/api/requests", headers=headers, json={"requesting_hospital_id": 1, "blood_group": "O+", "required_units": 1000, "urgency": "CRITICAL"})
    request_id = created.get_json()["data"]["id"]
    response = client.post("/api/algorithms/process-request", headers=headers, json={"request_id": request_id})
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "insufficient_inventory"
    detail = client.get(f"/api/requests/{request_id}", headers=headers).get_json()["data"]
    assert detail["status"] == "FAILED"
    assert detail["allocations"] == []


@pytest.mark.parametrize("blood_group", ["A+", "AB+", "O-"])
def test_process_request_handles_supported_compatibility_cases(client, blood_group):
    headers = auth_headers(client)
    created = client.post("/api/requests", headers=headers, json={"requesting_hospital_id": 1, "blood_group": blood_group, "required_units": 6, "urgency": "HIGH"})
    processed = client.post("/api/algorithms/process-request", headers=headers, json={"request_id": created.get_json()["data"]["id"]})
    assert processed.status_code == 200, processed.get_json()
    allocation = processed.get_json()["data"]["allocation"]
    assert allocation["allocated_units"] == 6
    assert allocation["status"] == "COMPLETED"


def test_competing_requests_never_drive_inventory_negative(client):
    headers = auth_headers(client)
    first = client.post("/api/requests", headers=headers, json={"requesting_hospital_id": 1, "blood_group": "O+", "required_units": 12, "urgency": "CRITICAL"}).get_json()["data"]["id"]
    second = client.post("/api/requests", headers=headers, json={"requesting_hospital_id": 1, "blood_group": "O+", "required_units": 12, "urgency": "CRITICAL"}).get_json()["data"]["id"]
    assert client.post("/api/algorithms/process-request", headers=headers, json={"request_id": first}).status_code == 200
    response = client.post("/api/algorithms/process-request", headers=headers, json={"request_id": second})
    assert response.status_code == 409
    inventory = client.get("/api/inventory", headers=headers).get_json()["data"]
    assert all(item["units_available"] >= 0 for item in inventory)
