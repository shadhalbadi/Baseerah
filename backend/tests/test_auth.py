"""Auth and per-user authorization — security-critical, so covered explicitly."""

from tests.conftest import auth_headers


def test_register_then_login_returns_token(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "name": "A", "password": "password123"})
    assert r.status_code == 201
    assert "hashed_password" not in r.json()  # never leak the hash

    r = client.post("/auth/login", data={"username": "a@b.com", "password": "password123"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_duplicate_email_rejected(client):
    body = {"email": "a@b.com", "name": "A", "password": "password123"}
    assert client.post("/auth/register", json=body).status_code == 201
    assert client.post("/auth/register", json=body).status_code == 409


def test_short_password_rejected(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "name": "A", "password": "short"})
    assert r.status_code == 422


def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={"email": "a@b.com", "name": "A", "password": "password123"})
    r = client.post("/auth/login", data={"username": "a@b.com", "password": "wrongpassword"})
    assert r.status_code == 401


def test_protected_endpoint_requires_token(client):
    assert client.get("/properties").status_code == 401
    assert client.post("/properties", json={"name": "Home"}).status_code == 401


def test_me_returns_current_user(client):
    headers = auth_headers(client, "me@b.com")
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "me@b.com"


def test_property_created_and_scoped_to_owner(client):
    headers = auth_headers(client)
    r = client.post("/properties", json={"name": "Home", "type": "villa"}, headers=headers)
    assert r.status_code == 201
    assert client.get("/properties", headers=headers).json()[0]["name"] == "Home"


def test_user_cannot_access_another_users_property(client):
    alice = auth_headers(client, "alice@b.com")
    bob = auth_headers(client, "bob@b.com")
    prop_id = client.post("/properties", json={"name": "Alice Home"}, headers=alice).json()["id"]

    # Bob must not see Alice's property — 404, not 403, so ids don't leak.
    assert client.get(f"/properties/{prop_id}", headers=bob).status_code == 404
    assert client.get("/properties", headers=bob).json() == []
    # Bob cannot add bills to Alice's property either.
    bill = {
        "utility_type": "water",
        "period_start": "2026-01-01",
        "period_end": "2026-01-31",
        "consumption": 10,
        "cost": 5,
    }
    assert client.post(f"/properties/{prop_id}/bills", json=bill, headers=bob).status_code == 404


def test_full_flow_analysis_with_auth(client):
    headers = auth_headers(client)
    prop_id = client.post("/properties", json={"name": "Home"}, headers=headers).json()["id"]
    months = [
        ("2026-01-01", "2026-01-31", 10),
        ("2026-02-01", "2026-02-28", 10),
        ("2026-03-01", "2026-03-31", 11),
        ("2026-04-01", "2026-04-30", 10),
        ("2026-05-01", "2026-05-31", 22),
    ]
    for s, e, cons in months:
        client.post(
            f"/properties/{prop_id}/bills",
            json={"utility_type": "water", "period_start": s, "period_end": e, "consumption": cons, "cost": cons * 2.5},
            headers=headers,
        )
    r = client.get(f"/properties/{prop_id}/analysis", params={"utility_type": "water"}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["latest"]["status"] == "anomaly"
    assert body["leak"]["suspected"] is True
