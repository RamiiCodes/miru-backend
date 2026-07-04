def test_register_user_returns_access_token(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_user_returns_access_token(client):
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "TestPassword123!",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "login@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_get_me_returns_authenticated_user(client):
    register_response = client.post(
        "/auth/register",
        json={
            "email": "me@example.com",
            "password": "TestPassword123!",
        },
    )

    token = register_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["email"] == "me@example.com"
    assert "id" in body
    assert "created_at" in body


def test_protected_endpoint_without_token_returns_401(client):
    response = client.get("/state")

    assert response.status_code == 401