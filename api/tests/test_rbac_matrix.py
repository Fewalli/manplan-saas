from fastapi.testclient import TestClient


def test_user_with_multiple_roles_can_access_admin_and_operational_routes(
    client: TestClient,
    admin_token: str,
):
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200


def test_user_without_required_role_gets_403(
    client: TestClient,
    technician_token: str,
):
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {technician_token}"},
    )
    assert response.status_code == 403