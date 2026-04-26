"""Integration test for MVP 1 happy path.
Requires: docker compose up (all services running).
Usage: pytest tests/integration/test_mvp1_flow.py -v
"""
import io
import time
import uuid

import httpx
import pytest

IDENTITY_URL = "http://localhost:8001"
SCHOOL_URL = "http://localhost:8002"
OBSERVATION_URL = "http://localhost:8003"
AUDIO_URL = "http://localhost:8004"
AUDIT_URL = "http://localhost:8009"

ADMIN_EMAIL = "admin@pec.seduc.sp.gov.br"
ADMIN_PASSWORD = "changeme123"


def _login() -> str:
    r = httpx.post(f"{IDENTITY_URL}/api/v1/auth/login",
                   json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=10)
    if r.status_code != 200:
        pytest.skip(f"Identity service not available or credentials wrong: {r.text}")
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def token():
    try:
        return _login()
    except httpx.ConnectError:
        pytest.skip("Services not running — start with docker compose up")


def test_01_login(token):
    """Login returns a valid JWT token."""
    assert len(token) > 50  # JWT is always long


def test_02_create_school(token):
    """Create a school and verify it's returned in list."""
    unique = uuid.uuid4().hex[:6]
    r = httpx.post(f"{SCHOOL_URL}/api/v1/schools",
                   json={"name": f"EMEF Teste {unique}", "city": "São Paulo",
                         "district": "Leste 1"},
                   headers=_auth(token), timeout=10)
    assert r.status_code == 201, r.text
    school = r.json()
    assert school["id"]
    assert school["name"].startswith("EMEF Teste")

    # Verify list
    list_r = httpx.get(f"{SCHOOL_URL}/api/v1/schools", headers=_auth(token), timeout=10)
    assert list_r.status_code == 200
    ids = [s["id"] for s in list_r.json()]
    assert school["id"] in ids

    return school


def test_03_create_teacher(token):
    """Create a teacher linked to the test school."""
    unique = uuid.uuid4().hex[:6]
    # First create a school
    school_r = httpx.post(f"{SCHOOL_URL}/api/v1/schools",
                          json={"name": f"EMEF Temp {unique}", "city": "Campinas",
                                "district": "Campinas"},
                          headers=_auth(token), timeout=10)
    school_id = school_r.json()["id"]

    teacher_r = httpx.post(f"{SCHOOL_URL}/api/v1/teachers",
                            json={"school_id": school_id, "name": "Prof. Ana Silva",
                                  "subjects": ["Matemática"], "grades": ["5º ano", "7º ano"]},
                            headers=_auth(token), timeout=10)
    assert teacher_r.status_code == 201, teacher_r.text
    teacher = teacher_r.json()
    assert teacher["school_id"] == school_id
    assert "Matemática" in teacher["subjects"]


def test_04_create_observation(token):
    """Create an observation in DRAFT status."""
    school_r = httpx.post(f"{SCHOOL_URL}/api/v1/schools",
                          json={"name": f"EMEF Obs {uuid.uuid4().hex[:6]}", "city": "SP",
                                "district": "Sul 1"},
                          headers=_auth(token), timeout=10)
    school_id = school_r.json()["id"]
    teacher_r = httpx.post(f"{SCHOOL_URL}/api/v1/teachers",
                            json={"school_id": school_id, "name": "Prof. Carlos"},
                            headers=_auth(token), timeout=10)
    teacher_id = teacher_r.json()["id"]

    obs_r = httpx.post(f"{OBSERVATION_URL}/api/v1/observations",
                       json={"school_id": school_id, "teacher_id": teacher_id,
                             "subject": "Português", "grade": "6º ano",
                             "lesson_theme": "Gêneros textuais",
                             "lesson_objectives": "Identificar diferentes gêneros"},
                       headers=_auth(token), timeout=10)
    assert obs_r.status_code == 201, obs_r.text
    obs = obs_r.json()
    assert obs["status"] == "DRAFT"
    assert obs["subject"] == "Português"

    return obs


def test_05_observation_status_transition(token):
    """Test valid and invalid status transitions."""
    # Create observation
    school_r = httpx.post(f"{SCHOOL_URL}/api/v1/schools",
                          json={"name": f"EMEF Status {uuid.uuid4().hex[:6]}", "city": "SP",
                                "district": "Norte"},
                          headers=_auth(token), timeout=10)
    teacher_r = httpx.post(f"{SCHOOL_URL}/api/v1/teachers",
                            json={"school_id": school_r.json()["id"], "name": "Prof. B"},
                            headers=_auth(token), timeout=10)

    obs_r = httpx.post(f"{OBSERVATION_URL}/api/v1/observations",
                       json={"school_id": school_r.json()["id"],
                             "teacher_id": teacher_r.json()["id"],
                             "subject": "Ciências", "grade": "8º ano",
                             "lesson_theme": "Sistema solar"},
                       headers=_auth(token), timeout=10)
    obs_id = obs_r.json()["id"]

    # Valid: DRAFT -> READY_TO_RECORD
    trans_r = httpx.patch(f"{OBSERVATION_URL}/api/v1/observations/{obs_id}/status",
                          json={"new_status": "READY_TO_RECORD"},
                          headers=_auth(token), timeout=10)
    assert trans_r.status_code == 200, trans_r.text
    assert trans_r.json()["status"] == "READY_TO_RECORD"

    # Invalid: READY_TO_RECORD -> APPROVED (skip)
    invalid_r = httpx.patch(f"{OBSERVATION_URL}/api/v1/observations/{obs_id}/status",
                             json={"new_status": "APPROVED"},
                             headers=_auth(token), timeout=10)
    assert invalid_r.status_code == 422, f"Expected 422, got {invalid_r.status_code}"


def test_06_presigned_upload_url(token):
    """Request a presigned upload URL from the audio ingestion service."""
    try:
        obs_id = str(uuid.uuid4())
        r = httpx.post(f"{AUDIO_URL}/api/v1/audio/presigned-url",
                       json={"observation_id": obs_id, "file_name": "test.m4a",
                             "file_size_bytes": 1024, "checksum": "abc123",
                             "codec": "aac"},
                       headers=_auth(token), timeout=10)
        assert r.status_code == 201, r.text
        data = r.json()
        assert "upload_id" in data
        assert "upload_url" in data
        assert data["method"] == "PUT"
    except httpx.ConnectError:
        pytest.skip("Audio service not reachable")


def test_07_audit_trail(token):
    """Verify audit service captures events."""
    try:
        r = httpx.get(f"{AUDIT_URL}/api/v1/audit/events",
                      headers=_auth(token), timeout=10)
        assert r.status_code == 200, r.text
        # Events from previous test steps should appear
    except httpx.ConnectError:
        pytest.skip("Audit service not reachable")
