import re


ALLOWED_ROLES = {"ADMIN", "HOSPITAL", "DISPATCHER", "USER"}
ALLOWED_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
ALLOWED_URGENCY = {"CRITICAL", "HIGH", "MEDIUM", "NORMAL"}
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def require_email(value: object) -> str:
    if not isinstance(value, str) or len(value) > 255 or not _EMAIL_PATTERN.fullmatch(value):
        raise ValueError("Invalid email")
    return value.strip().lower()


def require_role(value: object) -> str:
    if not isinstance(value, str) or value.upper() not in ALLOWED_ROLES:
        raise ValueError("Invalid role")
    return value.upper()


def require_blood_group(value: object) -> str:
    if not isinstance(value, str) or value.upper() not in ALLOWED_BLOOD_GROUPS:
        raise ValueError("Invalid blood group")
    return value.upper()


def require_urgency(value: object) -> str:
    if not isinstance(value, str) or value.upper() not in ALLOWED_URGENCY:
        raise ValueError("Invalid urgency")
    return value.upper()


def require_positive_id(value: object, field_name: str = "id") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"Invalid {field_name}")
    return value


def require_positive_units(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("Blood units must be a positive integer")
    return value
