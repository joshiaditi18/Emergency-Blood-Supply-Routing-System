from datetime import datetime, timedelta, timezone
from functools import wraps
from uuid import uuid4

import jwt
from flask import current_app, g, request

from backend.app import db
from backend.app.models import RevokedToken, User


class TokenError(ValueError):
    pass


def _secret(token_type: str) -> str:
    return current_app.config["JWT_SECRET_KEY"] if token_type == "access" else current_app.config["JWT_REFRESH_SECRET_KEY"]


def create_token(user: User, token_type: str) -> str:
    if token_type not in {"access", "refresh"}:
        raise ValueError("Invalid token type")
    now = datetime.now(timezone.utc)
    ttl = current_app.config[
        "JWT_ACCESS_EXPIRES_SECONDS" if token_type == "access" else "JWT_REFRESH_EXPIRES_SECONDS"
    ]
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "type": token_type,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(seconds=ttl),
    }
    return jwt.encode(payload, _secret(token_type), algorithm="HS256")


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, _secret(expected_type), algorithms=["HS256"], options={"require": ["sub", "type", "jti", "exp"]})
    except jwt.InvalidTokenError as exc:
        raise TokenError("Invalid or expired token") from exc
    if payload.get("type") != expected_type:
        raise TokenError("Invalid or expired token")
    if RevokedToken.query.filter_by(jti=payload["jti"]).first() is not None:
        raise TokenError("Invalid or expired token")
    return payload


def _authorization_token() -> str:
    value = request.headers.get("Authorization", "")
    scheme, _, token = value.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise TokenError("Authentication required")
    return token


def revoke_token(payload: dict) -> None:
    if RevokedToken.query.filter_by(jti=payload["jti"]).first() is None:
        db.session.add(RevokedToken(
            jti=payload["jti"],
            token_type=payload["type"],
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        ))
        db.session.commit()


def auth_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        from backend.app.errors import ApiError
        try:
            payload = decode_token(_authorization_token(), "access")
            user = db.session.get(User, int(payload["sub"]))
        except (TokenError, ValueError, TypeError):
            from backend.app.audit import record_audit
            record_audit("UNAUTHORIZED_ACCESS", "route", request.endpoint)
            db.session.commit()
            raise ApiError("Authentication required", 401, "authentication_required")
        if user is None:
            from backend.app.audit import record_audit
            record_audit("UNAUTHORIZED_ACCESS", "route", request.endpoint)
            db.session.commit()
            raise ApiError("Authentication required", 401, "authentication_required")
        g.current_user = user
        g.current_token = payload
        return view(*args, **kwargs)

    return wrapped


def require_role(*roles):
    allowed_roles = {role.upper() for role in roles}

    def decorator(view):
        @wraps(view)
        @auth_required
        def wrapped(*args, **kwargs):
            from backend.app.errors import ApiError
            if g.current_user.role not in allowed_roles:
                from backend.app.audit import record_audit
                record_audit("UNAUTHORIZED_ACCESS", "route", request.endpoint)
                raise ApiError("Forbidden", 403, "forbidden")
            return view(*args, **kwargs)

        return wrapped

    return decorator
