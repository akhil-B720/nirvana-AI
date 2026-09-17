import pytest
import io
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.auth import hash_password, verify_password, create_access_token

client = TestClient(app)

def test_password_hashing_and_verification():
    pw = "SuperSecurePassword123!"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_jwt_token_generation_and_validation():
    token = create_access_token(data={"sub": "test_officer", "role": "OFFICER"})
    assert isinstance(token, str)
    assert len(token) > 20

def test_login_success():
    resp = client.post("/api/v1/auth/login", json={
        "username": "officer",
        "password": "NirvanaOfficer2026!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "OFFICER"

def test_login_invalid_credentials():
    resp = client.post("/api/v1/auth/login", json={
        "username": "officer",
        "password": "IncorrectPassword!"
    })
    assert resp.status_code == 401

def test_unauthorized_file_upload_rejection():
    # Attempt upload without officer authorization
    file_bytes = io.BytesIO(b"Valid dummy bytes")
    resp = client.post(
        "/api/v1/evidence/upload",
        data={"project_id": "SYN-MP-001", "source": "FIELD_INSPECTION"},
        files={"file": ("test.jpg", file_bytes, "image/jpeg")}
    )
    assert resp.status_code == 403

def test_invalid_file_upload_rejection():
    # Attempt to upload an executable or unsupported file extension with Officer token
    token = create_access_token(data={"sub": "officer", "role": "OFFICER"})
    headers = {"Authorization": f"Bearer {token}"}
    file_bytes = io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00BinaryExeContent")
    resp = client.post(
        "/api/v1/evidence/upload",
        data={"project_id": "SYN-MP-001", "source": "FIELD_INSPECTION"},
        files={"file": ("malicious.exe", file_bytes, "application/x-dosexec")},
        headers=headers
    )
    assert resp.status_code == 400
    assert "Invalid file type" in resp.json()["detail"]
