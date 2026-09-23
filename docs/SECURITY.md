# Security Notes

Phase 2 adds the backend security foundation. All secrets are environment-only and `.env` files are ignored by Git.

## Passwords

Passwords are hashed with Argon2id using `argon2-cffi`. Passwords are never encrypted, returned, or written to audit metadata. Registration enforces a 12-128 character password with upper-case, lower-case, numeric, and special characters.

## JWTs and roles

Access tokens expire by configuration and are sent through the `Authorization: Bearer` header. Refresh tokens use a separate secret and expiration. Logout persists token JTIs in `revoked_tokens`, so revoked access and supplied refresh tokens cannot be reused.

Supported roles are `ADMIN`, `HOSPITAL`, `DISPATCHER`, and `USER`. Public registration can create only `USER` accounts. Backend authorization uses `auth_required` and `require_role`; frontend checks are not security controls.

## Encryption

`encrypt_data()` and `decrypt_data()` use AES-256-GCM with a fresh 12-byte nonce per operation and an authentication tag supplied by GCM. The key is URL-safe base64 containing exactly 32 random bytes from `ENCRYPTION_KEY`.

The current Phase 1 schema has no persisted phone number, emergency contact, or sensitive metadata field, so Phase 2 does not introduce an encrypted searchable column. When those fields are added, only non-searchable sensitive values should use this helper. IDs, foreign keys, status, timestamps, blood groups, and other indexed query fields remain plaintext.

## Request security

Authentication endpoints use configurable in-process rate limits. CORS requires explicit origins and rejects `*`. Responses include CSP, `X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy`. API errors use a consistent JSON shape and do not expose stack traces or secrets.

Security events are written to `audit_logs`: registration, login success/failure, logout, unauthorized access, and forbidden role access. Audit metadata redacts password, token, secret, and key fields.

The in-process limiter is suitable for the current single-process scaffold. A multi-instance deployment should replace it with a shared store such as Redis before production use.
