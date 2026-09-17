# NIRVANA - Security Architecture & Policy

## 1. Authentication & Role-Based Access Control (RBAC)
- **Token Mechanism:** Stateless JSON Web Tokens (JWT) signed via HMAC-SHA256 with cryptographically secure secret keys.
- **Password Protection:** Salting and hashing via `bcrypt` (work factor >= 12).
- **Enforced Roles:**
  1. `ADMIN`: Full administrative control, system settings, model promotion, user provisioning.
  2. `OFFICER`: Field verification triage, evidence uploads, ground-truth sign-off.
  3. `ANALYST`: Anomaly review, analytical queries, report generation.
  4. `VIEWER`: Read-only access to sanctioned projects, risk scores, and public dashboards.
- **Server-Side Enforcement:** Permissions are validated strictly on the backend FastAPI dependency injection layer (`Depends(require_role([...]))`), never relying on frontend visibility flags.

## 2. Input Validation & Injection Mitigation
- All relational interactions leverage **SQLAlchemy 2.0 ORM** parameterized queries, preventing SQL injection.
- Pydantic v2 schemas rigorously validate all request payloads, parsing types, enforcing non-negative monetary constraints, and checking bounded coordinates ($[-90, 90], [-180, 180]$).
- File uploads undergo multi-layer inspection:
  - Allowed MIME types: `image/jpeg`, `image/png`, `application/pdf`.
  - Binary magic byte validation (never trusting file extensions alone).
  - Maximum upload file size: 15MB.
  - Mandatory SHA-256 integrity checksumming.

## 3. Secret Management
- Secrets are loaded strictly from environment variables (`.env`).
- Defaults are provided only for local development testing.
- Passwords, keys, and tokens are prevented from being checked into version control via `.gitignore`.
