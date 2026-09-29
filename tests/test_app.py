import src.app as app_module
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def activities_data(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Learn chess strategies",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": ["existing@example.com"],
        }
    }
    monkeypatch.setattr(app_module, "activities", test_activities)
    return test_activities


@pytest.fixture
def client(activities_data):
    with TestClient(app_module.app, follow_redirects=False) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_current_activities(client, activities_data):
    # Arrange
    expected_activities = activities_data

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, activities_data):
    # Arrange
    email = "new@example.com"

    # Act
    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Signed up new@example.com for Chess Club"}
    assert email in activities_data["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client, activities_data):
    # Arrange
    email = "existing@example.com"

    # Act
    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activities_data["Chess Club"]["participants"] == [email]


def test_signup_rejects_unknown_activity(client, activities_data):
    # Arrange
    email = "new@example.com"

    # Act
    response = client.post(
        "/activities/Unknown Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities_data["Chess Club"]["participants"] == ["existing@example.com"]


def test_signup_rejects_full_activity(client, activities_data):
    # Arrange
    email = "new@example.com"
    activities_data["Chess Club"]["participants"] = [
        "first@example.com",
        "second@example.com",
    ]

    # Act
    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 409
    assert response.json() == {"detail": "Activity is full"}
    assert email not in activities_data["Chess Club"]["participants"]


def test_cancel_signup_removes_participant(client, activities_data):
    # Arrange
    email = "existing@example.com"

    # Act
    response = client.delete(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Canceled existing@example.com's signup for Chess Club"}
    assert email not in activities_data["Chess Club"]["participants"]


def test_cancel_signup_rejects_unknown_activity(client, activities_data):
    # Arrange
    email = "existing@example.com"

    # Act
    response = client.delete(
        "/activities/Unknown Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities_data["Chess Club"]["participants"] == [email]


def test_cancel_signup_rejects_unregistered_participant(client, activities_data):
    # Arrange
    email = "unknown@example.com"

    # Act
    response = client.delete(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activities_data["Chess Club"]["participants"] == ["existing@example.com"]
