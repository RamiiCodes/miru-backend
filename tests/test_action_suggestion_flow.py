from app.db.models.action_template import ActionTemplate
from app.db.repositories.user_repository import get_user_by_email


def _auth_headers(client, email: str) -> dict[str, str]:
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


def _seed_action_template(
    db_session,
    *,
    code: str,
    title: str,
    base_priority: int = 6,
) -> ActionTemplate:
    template = ActionTemplate(
        code=code,
        title=title,
        content=f"Test content for {title}.",
        action_type="reflection",
        base_priority=base_priority,
        base_confidence=0.7,
        minimum_score=0,
        is_active=True,
    )

    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)

    return template


def test_action_suggestion_generation_returns_empty_without_active_templates(
    client,
):
    headers = _auth_headers(client, "actions-no-templates@example.com")

    response = client.post(
        "/action-suggestions/generate",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_action_suggestion_generation_user_isolation_complete_and_dismiss(
    client,
    db_session,
):
    user_a_headers = _auth_headers(client, "actions-a@example.com")
    user_b_headers = _auth_headers(client, "actions-b@example.com")
    user_a = get_user_by_email(db=db_session, email="actions-a@example.com")
    user_b = get_user_by_email(db=db_session, email="actions-b@example.com")

    _seed_action_template(
        db_session,
        code="test_post_work_decompression_note",
        title="Try a short post-work decompression note",
        base_priority=8,
    )
    _seed_action_template(
        db_session,
        code="test_name_the_looping_thought",
        title="Name the looping thought",
        base_priority=5,
    )

    user_a_generate_response = client.post(
        "/action-suggestions/generate",
        headers=user_a_headers,
    )
    user_b_generate_response = client.post(
        "/action-suggestions/generate",
        headers=user_b_headers,
    )

    assert user_a_generate_response.status_code == 200
    assert user_b_generate_response.status_code == 200

    user_a_actions_by_code = {
        action["action_code"]: action
        for action in user_a_generate_response.json()
    }
    user_b_actions_by_code = {
        action["action_code"]: action
        for action in user_b_generate_response.json()
    }

    assert set(user_a_actions_by_code) == {
        "test_post_work_decompression_note",
        "test_name_the_looping_thought",
    }
    assert set(user_b_actions_by_code) == set(user_a_actions_by_code)

    for action in user_a_actions_by_code.values():
        assert action["user_id"] == str(user_a.id)
        assert action["source_type"] == "action_template"
        assert action["is_completed"] is False
        assert action["is_dismissed"] is False

    for action in user_b_actions_by_code.values():
        assert action["user_id"] == str(user_b.id)

    user_b_cannot_complete_user_a_response = client.patch(
        (
            "/action-suggestions/"
            f"{user_a_actions_by_code['test_post_work_decompression_note']['id']}"
            "/complete"
        ),
        headers=user_b_headers,
    )

    assert user_b_cannot_complete_user_a_response.status_code == 404

    user_a_list_response = client.get(
        "/action-suggestions",
        headers=user_a_headers,
    )
    user_b_list_response = client.get(
        "/action-suggestions",
        headers=user_b_headers,
    )

    assert user_a_list_response.status_code == 200
    assert user_b_list_response.status_code == 200

    assert {
        action["action_code"]
        for action in user_a_list_response.json()
    } == set(user_a_actions_by_code)
    assert {
        action["action_code"]
        for action in user_b_list_response.json()
    } == set(user_b_actions_by_code)

    complete_response = client.patch(
        (
            "/action-suggestions/"
            f"{user_a_actions_by_code['test_post_work_decompression_note']['id']}"
            "/complete"
        ),
        headers=user_a_headers,
    )
    dismiss_response = client.patch(
        (
            "/action-suggestions/"
            f"{user_a_actions_by_code['test_name_the_looping_thought']['id']}"
            "/dismiss"
        ),
        headers=user_a_headers,
    )

    assert complete_response.status_code == 200
    assert dismiss_response.status_code == 200

    completed_action = complete_response.json()
    dismissed_action = dismiss_response.json()

    assert completed_action["is_completed"] is True
    assert completed_action["completed_at"] is not None
    assert completed_action["is_dismissed"] is False

    assert dismissed_action["is_dismissed"] is True
    assert dismissed_action["dismissed_at"] is not None
    assert dismissed_action["is_completed"] is False

    active_user_a_response = client.get(
        "/action-suggestions",
        headers=user_a_headers,
    )

    assert active_user_a_response.status_code == 200
    assert active_user_a_response.json() == []

    all_user_a_response = client.get(
        "/action-suggestions?include_completed=true&include_dismissed=true",
        headers=user_a_headers,
    )

    assert all_user_a_response.status_code == 200

    all_user_a_actions_by_code = {
        action["action_code"]: action
        for action in all_user_a_response.json()
    }

    assert set(all_user_a_actions_by_code) == set(user_a_actions_by_code)
    assert all_user_a_actions_by_code["test_post_work_decompression_note"][
        "is_completed"
    ] is True
    assert all_user_a_actions_by_code["test_name_the_looping_thought"][
        "is_dismissed"
    ] is True
