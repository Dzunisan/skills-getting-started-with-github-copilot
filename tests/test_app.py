import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def restore_participants():
    original_participants = {
        activity_name: list(activity["participants"])
        for activity_name, activity in activities.items()
    }
    yield
    for activity_name, participants in original_participants.items():
        activities[activity_name]["participants"][:] = participants


def test_root_redirects_to_web_app(client):
    # Arrange
    root_url = "/"

    # Act
    response = client.get(root_url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    # Arrange
    activities_url = "/activities"

    # Act
    response = client.get(activities_url)

    # Assert
    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_participant(client):
    # Arrange
    email = "new-student@mergington.edu"
    signup_url = "/activities/Chess Club/signup"

    # Act
    response = client.post(signup_url, params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities_response.json()["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    email = "new-student@mergington.edu"
    signup_url = "/activities/Chess Club/signup"
    client.post(signup_url, params={"email": email})

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"


def test_signup_rejects_unknown_activity(client):
    # Arrange
    signup_url = "/activities/Unknown Club/signup"
    email = "student@mergington.edu"

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    # Arrange
    email = "new-student@mergington.edu"
    signup_url = "/activities/Chess Club/signup"
    client.post(signup_url, params={"email": email})

    # Act
    response = client.delete(signup_url, params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in activities_response.json()["Chess Club"]["participants"]


def test_unregister_rejects_missing_participant(client):
    # Arrange
    signup_url = "/activities/Chess Club/signup"
    email = "not-signed-up@mergington.edu"

    # Act
    response = client.delete(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up"


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    signup_url = "/activities/Unknown Club/signup"
    email = "student@mergington.edu"

    # Act
    response = client.delete(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
