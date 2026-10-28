def test_register_user_success(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Alex Mercer",
            "email": "alex@agency.com",
            "password": "securepassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "alex@agency.com"
    assert data["user"]["name"] == "Alex Mercer"

def test_register_duplicate_email_fails(client):
    payload = {
        "name": "Alex Mercer",
        "email": "alex_dup@agency.com",
        "password": "securepassword123"
    }
    resp1 = client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"]

def test_login_success(client):
    # Register first
    client.post(
        "/api/auth/register",
        json={
            "name": "Sarah Connor",
            "email": "sarah@tech.com",
            "password": "mysecretpassword"
        }
    )
    # Login
    response = client.post(
        "/api/auth/login",
        json={
            "email": "sarah@tech.com",
            "password": "mysecretpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "sarah@tech.com"

def test_login_invalid_credentials(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@tech.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401

def test_get_me_protected(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "hunter@example.com"
