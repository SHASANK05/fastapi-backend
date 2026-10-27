import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.models import User, RoleEnum
from app.core.security import get_password_hash

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_test_admin():
    """Ensure test admin account exists in database before tests run."""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@workforce.ai").first()
        if not admin:
            admin = User(
                email="admin@workforce.ai",
                hashed_password=get_password_hash("AdminPassword123"),
                role=RoleEnum.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
        else:
            # Update password to ensure match
            admin.hashed_password = get_password_hash("AdminPassword123")
            admin.is_active = True
            db.commit()
    finally:
        db.close()

def test_system_health():
    """Verify system status endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["system"] == "WorkForce AI Pro"

def test_admin_login_success():
    """Verify JWT authentication for Administrator."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@workforce.ai", "password": "AdminPassword123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "ADMIN"

def test_invalid_login():
    """Verify rejection of unauthorized credentials."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@workforce.ai", "password": "WrongPassword!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401

def test_rbac_unauthorized_access():
    """Verify protected endpoints reject requests without a JWT token."""
    response = client.get("/api/v1/predictions/analytics")
    assert response.status_code in [401, 403]

def test_full_analytics_pipeline():
    """Verify that authenticated Admin can access workforce analytics & predictions."""
    # 1. Login
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@workforce.ai", "password": "AdminPassword123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # 2. Get Analytics Dashboard Data
    res = client.get("/api/v1/predictions/analytics", headers=auth_header)
    assert res.status_code == 200
    data = res.json()
    assert "total_workforce_evaluated" in data
    assert "distribution" in data

    # 3. Check High Risk Interventions List
    res_high = client.get("/api/v1/predictions/high-risk", headers=auth_header)
    assert res_high.status_code == 200
    assert isinstance(res_high.json(), list)

    # 4. Check Audit Logs
    res_audit = client.get("/api/v1/audit-logs/?limit=10", headers=auth_header)
    assert res_audit.status_code == 200
    assert isinstance(res_audit.json(), list)
