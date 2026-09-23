from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from backend.app import db
from backend.app.audit import record_audit
from backend.app.errors import ApiError
from backend.app.models import RevokedToken, User
from backend.app.security.jwt import auth_required, create_token, decode_token, require_role, revoke_token
from backend.app.security.passwords import hash_password, verify_password
from backend.app.security.rate_limit import rate_limit
from backend.app.security.validation import require_email, require_role as validate_role


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _json_body() -> dict:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiError("Request body must be a JSON object", 400, "invalid_json")
    return payload


def _user_response(user: User) -> dict:
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}


@auth_bp.post("/register")
@rate_limit("RATE_LIMIT_REGISTER")
def register():
    payload = _json_body()
    try:
        email = require_email(payload.get("email"))
        password = payload.get("password")
        full_name = payload.get("full_name")
        requested_role = validate_role(payload.get("role", "USER"))
    except ValueError as exc:
        raise ApiError(str(exc), 400, "validation_error") from exc
    if requested_role != "USER":
        raise ApiError("Public registration only creates USER accounts", 400, "invalid_role")
    if not isinstance(full_name, str) or not 1 <= len(full_name.strip()) <= 160:
        raise ApiError("Invalid full name", 400, "validation_error")
    if User.query.filter_by(email=email).first() is not None:
        raise ApiError("Unable to create account", 409, "registration_failed")
    try:
        user = User(email=email, password_hash=hash_password(password), role="USER", full_name=full_name.strip())
        db.session.add(user)
        db.session.flush()
        record_audit("REGISTRATION", "user", user.id)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ApiError("Unable to create account", 409, "registration_failed") from exc
    return jsonify({"success": True, "user": _user_response(user)}), 201


@auth_bp.post("/login")
@rate_limit("RATE_LIMIT_LOGIN")
def login():
    payload = _json_body()
    try:
        email = require_email(payload.get("email"))
    except ValueError as exc:
        raise ApiError("Invalid credentials", 401, "invalid_credentials") from exc
    password = payload.get("password")
    user = User.query.filter_by(email=email).first()
    if user is None or not isinstance(password, str) or not verify_password(password, user.password_hash):
        record_audit("LOGIN_FAILURE", "user", metadata={"email": email})
        db.session.commit()
        raise ApiError("Invalid credentials", 401, "invalid_credentials")
    record_audit("LOGIN_SUCCESS", "user", user.id)
    db.session.commit()
    return jsonify({"success": True, "user": _user_response(user), "access_token": create_token(user, "access"), "refresh_token": create_token(user, "refresh")})


@auth_bp.post("/refresh")
@rate_limit("RATE_LIMIT_REFRESH")
def refresh():
    payload = _json_body()
    token = payload.get("refresh_token")
    if not isinstance(token, str):
        raise ApiError("Invalid refresh token", 401, "invalid_token")
    try:
        token_payload = decode_token(token, "refresh")
        user = db.session.get(User, int(token_payload["sub"]))
    except (ValueError, TypeError):
        user = None
    if user is None:
        raise ApiError("Invalid refresh token", 401, "invalid_token")
    return jsonify({"success": True, "access_token": create_token(user, "access")})


@auth_bp.get("/me")
@auth_required
def me():
    return jsonify({"success": True, "user": _user_response(g.current_user)})


@auth_bp.post("/logout")
@auth_required
def logout():
    revoke_token(g.current_token)
    payload = request.get_json(silent=True) or {}
    refresh_token = payload.get("refresh_token")
    if isinstance(refresh_token, str):
        try:
            refresh_payload = decode_token(refresh_token, "refresh")
            if refresh_payload["sub"] == str(g.current_user.id):
                db.session.add(RevokedToken(
                    jti=refresh_payload["jti"],
                    token_type="refresh",
                    expires_at=datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc),
                ))
        except (ValueError, TypeError):
            pass
    record_audit("LOGOUT", "user", g.current_user.id)
    db.session.commit()
    return jsonify({"success": True})


@auth_bp.get("/admin-check")
@require_role("ADMIN")
def admin_check():
    return jsonify({"success": True, "message": "admin access granted"})
