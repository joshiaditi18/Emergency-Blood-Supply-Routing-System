from datetime import datetime, timezone

from backend.app import db


def utc_now():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(40), nullable=False, index=True)
    full_name = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class RevokedToken(db.Model):
    __tablename__ = "revoked_tokens"
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(10), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    revoked_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class Hospital(db.Model):
    __tablename__ = "hospitals"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Numeric(9, 6), nullable=False)
    longitude = db.Column(db.Numeric(9, 6), nullable=False)
    address = db.Column(db.String(300))
    status = db.Column(db.String(30), nullable=False, default="ACTIVE", index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class HospitalConnection(db.Model):
    __tablename__ = "hospital_connections"
    id = db.Column(db.Integer, primary_key=True)
    source_hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False, index=True)
    destination_hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False, index=True)
    distance_km = db.Column(db.Numeric(10, 2), nullable=False)
    estimated_minutes = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    __table_args__ = (db.UniqueConstraint("source_hospital_id", "destination_hospital_id"),)


class BloodInventory(db.Model):
    __tablename__ = "blood_inventory"
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False, index=True)
    blood_group = db.Column(db.String(3), nullable=False, index=True)
    units_available = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    __table_args__ = (db.UniqueConstraint("hospital_id", "blood_group"), db.CheckConstraint("units_available >= 0"))


class BloodInventoryTransaction(db.Model):
    __tablename__ = "blood_inventory_transactions"
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey("blood_inventory.id"), nullable=False, index=True)
    request_id = db.Column(db.Integer, db.ForeignKey("blood_requests.id"), index=True)
    change_units = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class BloodRequest(db.Model):
    __tablename__ = "blood_requests"
    id = db.Column(db.Integer, primary_key=True)
    requesting_hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False, index=True)
    blood_group = db.Column(db.String(3), nullable=False, index=True)
    required_units = db.Column(db.Integer, nullable=False)
    urgency = db.Column(db.String(20), nullable=False, index=True)
    notes = db.Column(db.Text)
    priority_score = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(30), nullable=False, default="PENDING", index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    __table_args__ = (db.CheckConstraint("required_units > 0"),)


class Allocation(db.Model):
    __tablename__ = "allocations"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("blood_requests.id"), nullable=False, index=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False, index=True)
    units_allocated = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class Route(db.Model):
    __tablename__ = "routes"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("blood_requests.id"), nullable=False, index=True)
    source_hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False)
    destination_hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False)
    path_json = db.Column(db.JSON, nullable=False)
    distance_km = db.Column(db.Numeric(10, 2), nullable=False)
    estimated_minutes = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class Dispatch(db.Model):
    __tablename__ = "dispatches"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("blood_requests.id"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="CREATED", index=True)
    dispatched_at = db.Column(db.DateTime(timezone=True))
    delivered_at = db.Column(db.DateTime(timezone=True))


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    action = db.Column(db.String(60), nullable=False, index=True)
    entity = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.String(80))
    ip_address = db.Column(db.String(45))
    metadata_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    read_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
