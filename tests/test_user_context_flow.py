VALID_USER_CONTEXT = {
    "age_range_min": 30,
    "age_range_max": 35,
    "country": "France",
    "work_situation": "employed",
    "relationship_status": "single",
    "family_support_score": 6,
    "social_connection_score": 5,
    "work_stress_baseline": 8,
}


def _auth_headers(client, email: str = "user-context@example.com") -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201

    return {
        "Authorization": f"Bearer {response.json()['access_token']}",
    }


def test_get_user_context_returns_404_when_missing(client):
    headers = _auth_headers(client)

    response = client.get(
        "/user-context",
        headers=headers,
    )

    assert response.status_code == 404


def test_put_user_context_creates_context(client):
    headers = _auth_headers(client)

    response = client.put(
        "/user-context",
        json=VALID_USER_CONTEXT,
        headers=headers,
    )

    assert response.status_code == 200

    user_context = response.json()

    assert user_context["age_range_min"] == 30
    assert user_context["age_range_max"] == 35
    assert user_context["country"] == "France"
    assert user_context["work_situation"] == "employed"
    assert user_context["relationship_status"] == "single"
    assert user_context["family_support_score"] == 6
    assert user_context["social_connection_score"] == 5
    assert user_context["work_stress_baseline"] == 8


def test_get_user_context_returns_created_context(client):
    headers = _auth_headers(client, email="get-user-context@example.com")

    create_response = client.put(
        "/user-context",
        json=VALID_USER_CONTEXT,
        headers=headers,
    )

    assert create_response.status_code == 200

    get_response = client.get(
        "/user-context",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["user_id"] == create_response.json()["user_id"]


def test_patch_user_context_updates_partial_values(client):
    headers = _auth_headers(client, email="patch-user-context@example.com")

    create_response = client.put(
        "/user-context",
        json=VALID_USER_CONTEXT,
        headers=headers,
    )

    assert create_response.status_code == 200

    patch_response = client.patch(
        "/user-context",
        json={
            "social_connection_score": 2,
            "work_stress_baseline": 9,
        },
        headers=headers,
    )

    assert patch_response.status_code == 200

    user_context = patch_response.json()

    assert user_context["country"] == "France"
    assert user_context["social_connection_score"] == 2
    assert user_context["work_stress_baseline"] == 9


def test_patch_user_context_requires_existing_context(client):
    headers = _auth_headers(client, email="missing-patch-user-context@example.com")

    response = client.patch(
        "/user-context",
        json={
            "work_stress_baseline": 4,
        },
        headers=headers,
    )

    assert response.status_code == 404


def test_user_context_rejects_invalid_score(client):
    headers = _auth_headers(client, email="invalid-score-user-context@example.com")

    payload = {
        **VALID_USER_CONTEXT,
        "family_support_score": 11,
    }

    response = client.put(
        "/user-context",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 422


def test_user_context_rejects_invalid_age_range(client):
    headers = _auth_headers(client, email="invalid-age-user-context@example.com")

    payload = {
        **VALID_USER_CONTEXT,
        "age_range_min": 40,
        "age_range_max": 30,
    }

    response = client.put(
        "/user-context",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 422


def test_user_context_requires_authentication(client):
    get_response = client.get("/user-context")

    put_response = client.put(
        "/user-context",
        json=VALID_USER_CONTEXT,
    )

    patch_response = client.patch(
        "/user-context",
        json={
            "work_stress_baseline": 5,
        },
    )

    assert get_response.status_code == 401
    assert put_response.status_code == 401
    assert patch_response.status_code == 401


def test_users_only_see_their_own_user_context(client):
    user_a_headers = _auth_headers(client, email="context-a@example.com")
    user_b_headers = _auth_headers(client, email="context-b@example.com")

    user_a_response = client.put(
        "/user-context",
        json={
            **VALID_USER_CONTEXT,
            "country": "France",
        },
        headers=user_a_headers,
    )

    assert user_a_response.status_code == 200

    user_b_get_response = client.get(
        "/user-context",
        headers=user_b_headers,
    )

    assert user_b_get_response.status_code == 404

    user_b_response = client.put(
        "/user-context",
        json={
            **VALID_USER_CONTEXT,
            "country": "Tunisia",
        },
        headers=user_b_headers,
    )

    assert user_b_response.status_code == 200

    assert client.get(
        "/user-context",
        headers=user_a_headers,
    ).json()["country"] == "France"

    assert client.get(
        "/user-context",
        headers=user_b_headers,
    ).json()["country"] == "Tunisia"