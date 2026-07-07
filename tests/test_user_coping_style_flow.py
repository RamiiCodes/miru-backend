VALID_COPING_STYLE = {
    "preferred_coping_styles": ["writing", "reflection", "structure"],
    "disliked_coping_styles": ["breathing"],
    "writing_preference_score": 9,
    "movement_preference_score": 4,
    "breathing_preference_score": 2,
    "social_support_preference_score": 5,
    "reflection_preference_score": 8,
    "structure_preference_score": 9,
}


def _auth_headers(client, email: str = "coping-style@example.com") -> dict[str, str]:
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


def test_get_user_coping_style_returns_404_when_missing(client):
    headers = _auth_headers(client)

    response = client.get(
        "/user-coping-styles",
        headers=headers,
    )

    assert response.status_code == 404


def test_put_user_coping_style_creates_style(client):
    headers = _auth_headers(client)

    response = client.put(
        "/user-coping-styles",
        json=VALID_COPING_STYLE,
        headers=headers,
    )

    assert response.status_code == 200

    coping_style = response.json()

    assert coping_style["preferred_coping_styles"] == [
        "writing",
        "reflection",
        "structure",
    ]
    assert coping_style["disliked_coping_styles"] == ["breathing"]
    assert coping_style["writing_preference_score"] == 9
    assert coping_style["breathing_preference_score"] == 2
    assert coping_style["reflection_preference_score"] == 8


def test_get_user_coping_style_returns_created_style(client):
    headers = _auth_headers(client, email="get-coping-style@example.com")

    create_response = client.put(
        "/user-coping-styles",
        json=VALID_COPING_STYLE,
        headers=headers,
    )

    assert create_response.status_code == 200

    get_response = client.get(
        "/user-coping-styles",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["user_id"] == create_response.json()["user_id"]


def test_patch_user_coping_style_updates_partial_values(client):
    headers = _auth_headers(client, email="patch-coping-style@example.com")

    create_response = client.put(
        "/user-coping-styles",
        json=VALID_COPING_STYLE,
        headers=headers,
    )

    assert create_response.status_code == 200

    patch_response = client.patch(
        "/user-coping-styles",
        json={
            "movement_preference_score": 8,
            "disliked_coping_styles": ["social_support"],
        },
        headers=headers,
    )

    assert patch_response.status_code == 200

    coping_style = patch_response.json()

    assert coping_style["writing_preference_score"] == 9
    assert coping_style["movement_preference_score"] == 8
    assert coping_style["disliked_coping_styles"] == ["social_support"]


def test_patch_user_coping_style_requires_existing_style(client):
    headers = _auth_headers(client, email="missing-patch-coping-style@example.com")

    response = client.patch(
        "/user-coping-styles",
        json={
            "writing_preference_score": 7,
        },
        headers=headers,
    )

    assert response.status_code == 404


def test_user_coping_style_rejects_invalid_score(client):
    headers = _auth_headers(client, email="invalid-score-coping-style@example.com")

    payload = {
        **VALID_COPING_STYLE,
        "writing_preference_score": 11,
    }

    response = client.put(
        "/user-coping-styles",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 422


def test_user_coping_style_rejects_invalid_coping_style(client):
    headers = _auth_headers(client, email="invalid-style-coping-style@example.com")

    payload = {
        **VALID_COPING_STYLE,
        "preferred_coping_styles": ["writing", "unknown_style"],
    }

    response = client.put(
        "/user-coping-styles",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 422


def test_user_coping_style_deduplicates_styles(client):
    headers = _auth_headers(client, email="dedupe-coping-style@example.com")

    payload = {
        **VALID_COPING_STYLE,
        "preferred_coping_styles": ["writing", "writing", "reflection"],
    }

    response = client.put(
        "/user-coping-styles",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["preferred_coping_styles"] == ["writing", "reflection"]


def test_user_coping_style_requires_authentication(client):
    get_response = client.get("/user-coping-styles")

    put_response = client.put(
        "/user-coping-styles",
        json=VALID_COPING_STYLE,
    )

    patch_response = client.patch(
        "/user-coping-styles",
        json={
            "writing_preference_score": 5,
        },
    )

    assert get_response.status_code == 401
    assert put_response.status_code == 401
    assert patch_response.status_code == 401


def test_users_only_see_their_own_coping_styles(client):
    user_a_headers = _auth_headers(client, email="coping-a@example.com")
    user_b_headers = _auth_headers(client, email="coping-b@example.com")

    user_a_response = client.put(
        "/user-coping-styles",
        json={
            **VALID_COPING_STYLE,
            "preferred_coping_styles": ["writing"],
        },
        headers=user_a_headers,
    )

    assert user_a_response.status_code == 200

    user_b_get_response = client.get(
        "/user-coping-styles",
        headers=user_b_headers,
    )

    assert user_b_get_response.status_code == 404

    user_b_response = client.put(
        "/user-coping-styles",
        json={
            **VALID_COPING_STYLE,
            "preferred_coping_styles": ["movement"],
        },
        headers=user_b_headers,
    )

    assert user_b_response.status_code == 200

    assert client.get(
        "/user-coping-styles",
        headers=user_a_headers,
    ).json()["preferred_coping_styles"] == ["writing"]

    assert client.get(
        "/user-coping-styles",
        headers=user_b_headers,
    ).json()["preferred_coping_styles"] == ["movement"]