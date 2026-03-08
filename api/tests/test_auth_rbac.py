from fastapi.testclient import TestClient


def test_login_requires_valid_credentials(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "naoexiste@manplan.com", "password": "senhaerrada"},
    )
    assert response.status_code == 401


def test_protected_route_requires_token(client: TestClient):
    response = client.get("/api/v1/users")
    assert response.status_code == 401