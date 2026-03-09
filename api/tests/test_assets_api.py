def login(client, email: str, password: str):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_list_assets_returns_area_context(client):
    token = login(client, "multiplo@teste.com", "Senha123!")
    response = client.get("/api/v1/assets", headers=auth_headers(token))
    assert response.status_code == 200, response.text

    data = response.json()
    assert len(data) >= 1
    assert data[0]["area_code"] == "AREA-01"
    assert data[0]["area_name"] == "Área Teste"


def test_get_asset_detail_returns_recent_work_orders(client, seeded_db):
    requester_token = login(client, "solicitante@teste.com", "Senha123!")
    admin_token = login(client, "multiplo@teste.com", "Senha123!")

    create_response = client.post(
        "/api/v1/work-orders",
        json={
            "type": "OSC",
            "asset_id": seeded_db["asset"].id,
            "description": "Histórico do ativo",
        },
        headers=auth_headers(requester_token),
    )
    assert create_response.status_code == 201, create_response.text

    response = client.get(
        f"/api/v1/assets/{seeded_db['asset'].id}",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["code"] == "ATV-001"
    assert data["area_code"] == "AREA-01"
    assert len(data["recent_work_orders"]) >= 1
    assert data["recent_work_orders"][0]["code"].startswith("OSC")


def test_get_asset_detail_returns_404_for_other_tenant_asset(client, db_session):
    from app.core.security import get_password_hash
    from app.models.area import Area
    from app.models.asset import Asset
    from app.models.role import Role, UserRole
    from app.models.tenant import Tenant
    from app.models.user import User

    other_tenant = Tenant(name="Tenant Outro", slug="tenant-outro", is_active=True)
    db_session.add(other_tenant)
    db_session.flush()

    other_role = Role(tenant_id=other_tenant.id, code="admin_tenant", name="Admin Outro", is_active=True)
    db_session.add(other_role)
    db_session.flush()

    other_user = User(
        tenant_id=other_tenant.id,
        full_name="Admin Outro",
        email="outro@teste.com",
        password_hash=get_password_hash("Senha123!"),
        is_active=True,
    )
    db_session.add(other_user)
    db_session.flush()

    db_session.add(UserRole(user_id=other_user.id, role_id=other_role.id))
    db_session.flush()

    other_area = Area(
        tenant_id=other_tenant.id,
        code="AREA-99",
        name="Área Outro Tenant",
        is_active=True,
    )
    db_session.add(other_area)
    db_session.flush()

    other_asset = Asset(
        tenant_id=other_tenant.id,
        area_id=other_area.id,
        code="ATV-999",
        name="Ativo Outro Tenant",
        location="Linha 99",
        is_active=True,
    )
    db_session.add(other_asset)
    db_session.commit()

    token = login(client, "multiplo@teste.com", "Senha123!")
    response = client.get(
        f"/api/v1/assets/{other_asset.id}",
        headers=auth_headers(token),
    )
    assert response.status_code == 404