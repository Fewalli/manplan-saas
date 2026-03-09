def login(client, email: str, password: str):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def create_os(client, token, payload):
    response = client.post("/api/v1/work-orders", json=payload, headers=auth_headers(token))
    assert response.status_code == 201, response.text
    return response.json()


def test_technician_cannot_execute_two_work_orders(client, seeded_db):
    requester_token = login(client, "solicitante@teste.com", "Senha123!")
    technician_token = login(client, "tecnico@teste.com", "Senha123!")

    wo1 = create_os(
        client,
        requester_token,
        {"type": "OSC", "asset_id": seeded_db["asset"].id, "description": "Falha no motor"},
    )
    wo2 = create_os(
        client,
        requester_token,
        {"type": "OSC", "asset_id": seeded_db["asset"].id, "description": "Falha no inversor"},
    )

    r1 = client.post(f"/api/v1/work-orders/{wo1['id']}/start", headers=auth_headers(technician_token))
    assert r1.status_code == 200, r1.text

    r2 = client.post(f"/api/v1/work-orders/{wo2['id']}/start", headers=auth_headers(technician_token))
    assert r2.status_code == 400
    assert "Você já está em execução na OS" in r2.json()["detail"]


def test_suspend_requires_reason_and_description(client, seeded_db):
    requester_token = login(client, "solicitante@teste.com", "Senha123!")
    technician_token = login(client, "tecnico@teste.com", "Senha123!")

    wo = create_os(
        client,
        requester_token,
        {"type": "OSC", "asset_id": seeded_db["asset"].id, "description": "Falha hidráulica"},
    )
    client.post(f"/api/v1/work-orders/{wo['id']}/start", headers=auth_headers(technician_token))

    response = client.post(
        f"/api/v1/work-orders/{wo['id']}/suspend",
        json={"reason": "", "description": ""},
        headers=auth_headers(technician_token),
    )
    assert response.status_code == 422


def test_finalize_osc_requires_downtime_gt_one_minute(client, seeded_db):
    requester_token = login(client, "solicitante@teste.com", "Senha123!")
    technician_token = login(client, "tecnico@teste.com", "Senha123!")

    wo = create_os(
        client,
        requester_token,
        {"type": "OSC", "asset_id": seeded_db["asset"].id, "description": "Falha pneumática"},
    )
    client.post(f"/api/v1/work-orders/{wo['id']}/start", headers=auth_headers(technician_token))

    response = client.post(
        f"/api/v1/work-orders/{wo['id']}/finalize",
        json={
            "happened_what": "travou",
            "happened_why": "desgaste",
            "action_taken": "ajuste",
            "technician_downtime": {"days": 0, "hours": 0, "minutes": 1},
        },
        headers=auth_headers(technician_token),
    )
    assert response.status_code == 400
    assert "maior que 1 minuto" in response.json()["detail"]


def test_close_not_met_creates_revision(client, seeded_db):
    requester_token = login(client, "solicitante@teste.com", "Senha123!")
    technician_token = login(client, "tecnico@teste.com", "Senha123!")

    wo = create_os(
        client,
        requester_token,
        {"type": "OSC", "asset_id": seeded_db["asset"].id, "description": "Falha elétrica"},
    )
    client.post(f"/api/v1/work-orders/{wo['id']}/start", headers=auth_headers(technician_token))

    finalize = client.post(
        f"/api/v1/work-orders/{wo['id']}/finalize",
        json={
            "happened_what": "queima de contato",
            "happened_why": "sobrecorrente",
            "action_taken": "substituição",
            "technician_downtime": {"days": 0, "hours": 0, "minutes": 2},
        },
        headers=auth_headers(technician_token),
    )
    assert finalize.status_code == 200, finalize.text

    close = client.post(
        f"/api/v1/work-orders/{wo['id']}/close",
        json={
            "met_expectation": False,
            "requester_downtime": {"days": 0, "hours": 0, "minutes": 10},
        },
        headers=auth_headers(requester_token),
    )
    assert close.status_code == 200, close.text

    listing = client.get("/api/v1/work-orders", headers=auth_headers(requester_token))
    assert listing.status_code == 200
    codes = [item["code"] for item in listing.json()]
    assert any(code.endswith("-R1") for code in codes)
def test_create_work_order_requires_asset_id(client):
    requester_token = login(client, "solicitante@teste.com", "Senha123!")

    response = client.post(
        "/api/v1/work-orders",
        json={"type": "OSM", "description": "Inspeção sem ativo"},
        headers=auth_headers(requester_token),
    )
    assert response.status_code == 422


def test_create_work_order_rejects_inactive_asset(client, seeded_db, db_session):
    from app.models.asset import Asset

    requester_token = login(client, "solicitante@teste.com", "Senha123!")
    asset = seeded_db["asset"]
    asset.is_active = False
    db_session.add(asset)
    db_session.commit()

    response = client.post(
        "/api/v1/work-orders",
        json={"type": "OSC", "asset_id": asset.id, "description": "Falha no motor"},
        headers=auth_headers(requester_token),
    )
    assert response.status_code == 400
    assert "Ativo inativo" in response.json()["detail"]


def test_create_asset_rejects_duplicate_code_same_tenant(client):
    admin_token = login(client, "multiplo@teste.com", "Senha123!")

    response = client.post(
        "/api/v1/assets",
        json={
            "area_id": 1,
            "code": "ATV-001",
            "name": "Ativo duplicado",
            "location": "Linha X",
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 400
    assert "Já existe um ativo com este código" in response.json()["detail"]


def test_create_area_rejects_duplicate_code_same_tenant(client):
    admin_token = login(client, "multiplo@teste.com", "Senha123!")

    response = client.post(
        "/api/v1/areas",
        json={
            "code": "AREA-01",
            "name": "Área duplicada",
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 400
    assert "Já existe uma área com este código" in response.json()["detail"]


def test_list_assets_returns_area_metadata(client):
    admin_token = login(client, "multiplo@teste.com", "Senha123!")

    response = client.get("/api/v1/assets", headers=auth_headers(admin_token))
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "area_code" in data[0]
    assert "area_name" in data[0]