import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.security.hashing import verify_password, get_password_hash
from backend.app.security.jwt_handler import create_access_token, decode_access_token

@pytest.mark.asyncio
async def test_password_hashing():
    pwd = "MySecurePassword123!"
    h = get_password_hash(pwd)
    assert verify_password(pwd, h) is True
    assert verify_password("WrongPassword", h) is False

@pytest.mark.asyncio
async def test_jwt_token_flow():
    payload = {"sub": "1", "email": "test@neurobroker.org", "role": "admin"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "1"
    assert decoded["email"] == "test@neurobroker.org"
    assert decoded["role"] == "admin"

@pytest.mark.asyncio
async def test_user_registration_and_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register
        reg_payload = {
            "name": "Alex Developer",
            "email": f"alex_{pytest.__version__}@test.org",
            "password": "Password123!",
            "role": "admin"
        }
        res = await client.post("/auth/register", json=reg_payload)
        assert res.status_code in (201, 400) # 201 if first time, 400 if already exists
        
        # Login
        login_payload = {
            "email": reg_payload["email"],
            "password": reg_payload["password"]
        }
        res = await client.post("/auth/login", json=login_payload)
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["user"]["email"] == reg_payload["email"]
