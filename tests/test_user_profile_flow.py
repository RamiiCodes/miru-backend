def _auth_headers(client, email: str = "profile@example.com") -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


def test_get_profile_returns_404_when_missing(client):
    headers = _auth_headers(client)

    response = client.get(
        "/profile",
        headers=headers,
    )

    assert response.status_code == 404


def test_patch_profile_creates_profile(client):
    headers = _auth_headers(client)

    response = client.patch(
        "/profile",
        json={
            "display_name": "Rami",
            "birth_year": 1994,
            "country": "France",
            "gender": "male",
            "living_situation": "alone",
            "relationship_status": "single",
            "work_status": "employed",
            "main_life_context": ["work_stress", "self_understanding"],
            "interests": ["technology", "fitness", "anime"],
            "preferred_reflection_style": "direct",
            "onboarding_completed": True,
        },
        headers=headers,
    )

    assert response.status_code == 200

    profile = response.json()

    assert profile["display_name"] == "Rami"
    assert profile["birth_year"] == 1994
    assert profile["country"] == "France"
    assert profile["preferred_reflection_style"] == "direct"
    assert profile["onboarding_completed"] is True
    assert profile["main_life_context"] == ["work_stress", "self_understanding"]
    assert profile["interests"] == ["technology", "fitness", "anime"]


def test_get_profile_returns_created_profile(client):
    headers = _auth_headers(client)

    create_response = client.patch(
        "/profile",
        json={
            "display_name": "Rami",
            "country": "France",
            "preferred_reflection_style": "gentle",
        },
        headers=headers,
    )

    assert create_response.status_code == 200

    response = client.get(
        "/profile",
        headers=headers,
    )

    assert response.status_code == 200

    profile = response.json()

    assert profile["id"] == create_response.json()["id"]
    assert profile["display_name"] == "Rami"
    assert profile["country"] == "France"
    assert profile["preferred_reflection_style"] == "gentle"


def test_patch_profile_partial_update_keeps_existing_values(client):
    headers = _auth_headers(client)

    first_response = client.patch(
        "/profile",
        json={
            "display_name": "Rami",
            "country": "France",
            "preferred_reflection_style": "balanced",
            "onboarding_completed": False,
        },
        headers=headers,
    )

    assert first_response.status_code == 200

    second_response = client.patch(
        "/profile",
        json={
            "preferred_reflection_style": "direct",
            "onboarding_completed": True,
        },
        headers=headers,
    )

    assert second_response.status_code == 200

    profile = second_response.json()

    assert profile["display_name"] == "Rami"
    assert profile["country"] == "France"
    assert profile["preferred_reflection_style"] == "direct"
    assert profile["onboarding_completed"] is True


def test_profile_requires_authentication(client):
    get_response = client.get("/profile")
    patch_response = client.patch(
        "/profile",
        json={
            "display_name": "Rami",
        },
    )

    assert get_response.status_code == 401
    assert patch_response.status_code == 401


def test_users_only_see_their_own_profiles(client):
    user_a_headers = _auth_headers(client, email="profile-a@example.com")
    user_b_headers = _auth_headers(client, email="profile-b@example.com")

    user_a_response = client.patch(
        "/profile",
        json={
            "display_name": "User A",
            "country": "France",
        },
        headers=user_a_headers,
    )

    assert user_a_response.status_code == 200

    user_b_get_response = client.get(
        "/profile",
        headers=user_b_headers,
    )

    assert user_b_get_response.status_code == 404

    user_b_response = client.patch(
        "/profile",
        json={
            "display_name": "User B",
            "country": "Tunisia",
        },
        headers=user_b_headers,
    )

    assert user_b_response.status_code == 200

    user_a_get_response = client.get(
        "/profile",
        headers=user_a_headers,
    )

    user_b_get_response = client.get(
        "/profile",
        headers=user_b_headers,
    )

    assert user_a_get_response.status_code == 200
    assert user_b_get_response.status_code == 200

    assert user_a_get_response.json()["display_name"] == "User A"
    assert user_a_get_response.json()["country"] == "France"

    assert user_b_get_response.json()["display_name"] == "User B"
    assert user_b_get_response.json()["country"] == "Tunisia"