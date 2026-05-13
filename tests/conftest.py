"""Pytest configuration and fixtures for the API tests."""

import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset the activities database to initial state before each test."""
    # Store the initial state
    initial_activities = deepcopy(activities)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(deepcopy(initial_activities))


@pytest.fixture
def mock_activities(reset_activities):
    """Provide access to the activities dictionary for test setup."""
    return activities
