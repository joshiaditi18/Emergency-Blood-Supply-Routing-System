import re

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


_password_hasher = PasswordHasher()
_PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).+$")


def validate_password(password: object) -> str:
    if not isinstance(password, str) or len(password) < 12 or len(password) > 128:
        raise ValueError("Password must be between 12 and 128 characters")
    if not _PASSWORD_PATTERN.match(password):
        raise ValueError("Password must include upper, lower, digit, and special characters")
    return password


def hash_password(password: object) -> str:
    return _password_hasher.hash(validate_password(password))


def verify_password(password: object, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError, TypeError):
        return False
