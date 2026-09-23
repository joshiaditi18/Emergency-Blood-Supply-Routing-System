import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_NONCE_SIZE = 12
_KEY_SIZE = 32


def _key_from_environment() -> bytes:
    encoded_key = os.getenv("ENCRYPTION_KEY")
    if not encoded_key:
        raise RuntimeError("ENCRYPTION_KEY is required for field encryption")
    try:
        key = base64.urlsafe_b64decode(encoded_key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise RuntimeError("ENCRYPTION_KEY must be URL-safe base64") from exc
    if len(key) != _KEY_SIZE:
        raise RuntimeError("ENCRYPTION_KEY must decode to exactly 32 bytes")
    return key


def encrypt_data(plaintext: str, *, associated_data: bytes | None = None) -> str:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = AESGCM(_key_from_environment()).encrypt(
        nonce,
        plaintext.encode("utf-8"),
        associated_data,
    )
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")


def decrypt_data(token: str, *, associated_data: bytes | None = None) -> str:
    try:
        payload = base64.urlsafe_b64decode(token.encode("ascii"))
        nonce, ciphertext = payload[:_NONCE_SIZE], payload[_NONCE_SIZE:]
        plaintext = AESGCM(_key_from_environment()).decrypt(nonce, ciphertext, associated_data)
    except (InvalidTag, ValueError, TypeError, UnicodeDecodeError) as exc:
        raise ValueError("Encrypted data failed authentication") from exc
    return plaintext.decode("utf-8")
