def _auth_headers(client, email: str = "user-goals@example.com") -> dict[str, str]:
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


def _create_goal(client, headers: dict[str, str]) -> dict:
    response = client.post(
        "/user-goals",
        json={
            "category": "stress_management",
            "title": "Reduce work stress",
            "description": "I want to understand and reduce stress linked to work.",
            "priority": 8,
            "time_horizon": "medium_term",
        },
        headers=headers,
    )

    assert response.status_code == 201

    return response.json()


def test_create_user_goal(client):
    headers = _auth_headers(client)

    goal = _create_goal(client, headers)

    assert goal["source_type"] == "manual"
    assert goal["source_id"] is None
    assert goal["category"] == "stress_management"
    assert goal["title"] == "Reduce work stress"
    assert goal["description"] == "I want to understand and reduce stress linked to work."
    assert goal["priority"] == 8
    assert goal["time_horizon"] == "medium_term"
    assert goal["status"] == "active"
    assert goal["progress"] == 0.0
    assert goal["confidence"] == 1.0
    assert goal["completed_at"] is None


def test_list_user_goals(client):
    headers = _auth_headers(client, email="list-user-goals@example.com")

    goal = _create_goal(client, headers)

    response = client.get(
        "/user-goals",
        headers=headers,
    )

    assert response.status_code == 200

    goals = response.json()

    assert len(goals) == 1
    assert goals[0]["id"] == goal["id"]


def test_update_user_goal(client):
    headers = _auth_headers(client, email="update-user-goal@example.com")

    goal = _create_goal(client, headers)

    response = client.patch(
        f"/user-goals/{goal['id']}",
        json={
            "title": "Reduce stress gently",
            "priority": 9,
            "progress": 0.4,
        },
        headers=headers,
    )

    assert response.status_code == 200

    updated_goal = response.json()

    assert updated_goal["title"] == "Reduce stress gently"
    assert updated_goal["priority"] == 9
    assert updated_goal["progress"] == 0.4


def test_complete_user_goal(client):
    headers = _auth_headers(client, email="complete-user-goal@example.com")

    goal = _create_goal(client, headers)

    response = client.patch(
        f"/user-goals/{goal['id']}/complete",
        headers=headers,
    )

    assert response.status_code == 200

    completed_goal = response.json()

    assert completed_goal["status"] == "completed"
    assert completed_goal["progress"] == 1.0
    assert completed_goal["completed_at"] is not None

    active_response = client.get(
        "/user-goals",
        headers=headers,
    )

    assert active_response.status_code == 200
    assert active_response.json() == []

    all_response = client.get(
        "/user-goals?include_inactive=true",
        headers=headers,
    )

    assert all_response.status_code == 200
    assert len(all_response.json()) == 1


def test_archive_user_goal(client):
    headers = _auth_headers(client, email="archive-user-goal@example.com")

    goal = _create_goal(client, headers)

    response = client.patch(
        f"/user-goals/{goal['id']}/archive",
        headers=headers,
    )

    assert response.status_code == 200

    archived_goal = response.json()

    assert archived_goal["status"] == "archived"

    active_response = client.get(
        "/user-goals",
        headers=headers,
    )

    assert active_response.status_code == 200
    assert active_response.json() == []


def test_user_goals_require_authentication(client):
    response = client.get("/user-goals")

    assert response.status_code == 401


def test_users_only_see_their_own_goals(client):
    user_a_headers = _auth_headers(client, email="user-goals-a@example.com")
    user_b_headers = _auth_headers(client, email="user-goals-b@example.com")

    _create_goal(client, user_a_headers)

    user_a_response = client.get(
        "/user-goals",
        headers=user_a_headers,
    )

    user_b_response = client.get(
        "/user-goals",
        headers=user_b_headers,
    )

    assert user_a_response.status_code == 200
    assert user_b_response.status_code == 200

    assert len(user_a_response.json()) == 1
    assert user_b_response.json() == []