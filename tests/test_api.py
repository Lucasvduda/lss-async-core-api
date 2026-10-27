import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_login_refresh_and_items_flow(client):
    reg = await client.post(
        "/v1/auth/register",
        json={
            "email": "lucas@lss.dev",
            "password": "senhaforte",
            "full_name": "Lucas Viana",
            "role": "admin",
        },
    )
    assert reg.status_code == 201
    assert reg.json()["email"] == "lucas@lss.dev"

    login = await client.post(
        "/v1/auth/login",
        json={"email": "lucas@lss.dev", "password": "senhaforte"},
    )
    assert login.status_code == 200
    tokens = login.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me = await client.get("/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "admin"

    created = await client.post(
        "/v1/items",
        headers=headers,
        json={"title": "Pedido 1", "description": "demo", "status": "open"},
    )
    assert created.status_code == 201
    item_id = created.json()["id"]

    listed = await client.get("/v1/items?page=1&page_size=10&status=open&q=Pedido", headers=headers)
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] >= 1
    assert body["items"][0]["title"] == "Pedido 1"

    got = await client.get(f"/v1/items/{item_id}", headers=headers)
    assert got.status_code == 200

    csv_content = "title,description,status\nImport A,desc,open\nImport B,desc,done\n"
    imported = await client.post(
        "/v1/items/import/csv",
        headers=headers,
        files={"file": ("items.csv", csv_content, "text/csv")},
    )
    assert imported.status_code == 200
    assert imported.json()["imported"] == 2

    refreshed = await client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    assert "access_token" in refreshed.json()


@pytest.mark.asyncio
async def test_rbac_viewer_cannot_create(client):
    await client.post(
        "/v1/auth/register",
        json={
            "email": "viewer@lss.dev",
            "password": "senhaforte",
            "full_name": "Viewer",
            "role": "viewer",
        },
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": "viewer@lss.dev", "password": "senhaforte"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    created = await client.post(
        "/v1/items",
        headers=headers,
        json={"title": "X", "status": "open"},
    )
    assert created.status_code == 403
