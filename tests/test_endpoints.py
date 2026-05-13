"""Tests for the Mergington High School Activities API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_redirect(self, client):
        """Test that root redirects to static index.html."""
        # Arrange & Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint."""

    def test_get_activities_success(self, client, mock_activities):
        """Test that GET /activities returns all activities with correct structure."""
        # Arrange
        expected_activities = list(mock_activities.keys())
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == len(expected_activities)
        
        # Verify each activity has required fields
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_includes_all_required_activities(self, client):
        """Test that all expected activities are present."""
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        required_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Art Club",
            "Drama Club",
            "Science Club",
            "Debate Team",
        ]
        for activity in required_activities:
            assert activity in data


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success_new_participant(self, client, mock_activities):
        """Test successful signup for a new participant."""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        initial_count = len(mock_activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        assert email in mock_activities[activity_name]["participants"]
        assert len(mock_activities[activity_name]["participants"]) == initial_count + 1

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity returns 404."""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_signup_already_registered(self, client, mock_activities):
        """Test that signing up twice returns 400 error."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in participants
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already" in data["detail"].lower()

    def test_signup_multiple_different_emails(self, client, mock_activities):
        """Test multiple different students can sign up for same activity."""
        # Arrange
        activity_name = "Programming Class"
        new_emails = ["alice@mergington.edu", "bob@mergington.edu"]
        
        # Act & Assert
        for email in new_emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
            assert email in mock_activities[activity_name]["participants"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""

    def test_unregister_success(self, client, mock_activities):
        """Test successful unregistration of a participant."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in participants
        initial_count = len(mock_activities[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        assert email not in mock_activities[activity_name]["participants"]
        assert len(mock_activities[activity_name]["participants"]) == initial_count - 1

    def test_unregister_activity_not_found(self, client):
        """Test unregister for non-existent activity returns 404."""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_unregister_not_signed_up(self, client):
        """Test unregister for participant not in activity returns 400."""
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"].lower()

    def test_unregister_then_can_register_again(self, client, mock_activities):
        """Test that after unregistering, a student can register again."""
        # Arrange
        activity_name = "Art Club"
        email = "isabella@mergington.edu"
        
        # Act - First unregister
        response1 = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        assert email not in mock_activities[activity_name]["participants"]
        
        # Act - Then register again
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response2.status_code == 200
        assert email in mock_activities[activity_name]["participants"]


class TestDataIntegrity:
    """Tests to ensure data integrity across operations."""

    def test_signup_and_unregister_maintains_other_participants(self, client, mock_activities):
        """Test that operations on one participant don't affect others."""
        # Arrange
        activity_name = "Science Club"
        original_participants = mock_activities[activity_name]["participants"].copy()
        new_email = "newscientist@mergington.edu"
        
        # Act - Sign up new participant
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert - Original participants still there
        for participant in original_participants:
            assert participant in mock_activities[activity_name]["participants"]
        
        # Act - Unregister new participant
        client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert - Original participants still there, new one removed
        assert mock_activities[activity_name]["participants"] == original_participants

    def test_operations_are_isolated_between_activities(self, client, mock_activities):
        """Test that signup to one activity doesn't affect another."""
        # Arrange
        email = "testuser@mergington.edu"
        
        # Act - Sign up to one activity
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Assert - User only in Chess Club, not in others
        assert response.status_code == 200
        assert email in mock_activities["Chess Club"]["participants"]
        assert email not in mock_activities["Programming Class"]["participants"]
        assert email not in mock_activities["Art Club"]["participants"]
