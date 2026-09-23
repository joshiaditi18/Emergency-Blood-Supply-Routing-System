from flask import request

from backend.app import db
from backend.app.models import AuditLog


_SECRET_KEYS = {"password", "password_hash", "token", "access_token", "refresh_token", "secret", "key"}


def _safe_metadata(metadata: dict | None) -> dict | None:
    if metadata is None:
        return None
    return {key: "[REDACTED]" if key.lower() in _SECRET_KEYS else value for key, value in metadata.items()}


def record_audit(action: str, entity: str, entity_id: str | int | None = None, metadata: dict | None = None, user_id: int | None = None) -> None:
    from flask import g
    db.session.add(AuditLog(
        user_id=user_id if user_id is not None else getattr(getattr(g, "current_user", None), "id", None),
        action=action,
        entity=entity,
        entity_id=str(entity_id) if entity_id is not None else None,
        ip_address=request.remote_addr,
        metadata_json=_safe_metadata(metadata),
    ))
