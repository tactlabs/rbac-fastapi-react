from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import app  # Import FastAPI app

client = TestClient(app)  # Pass app as a positional argument, not keyword argument

def test_register_user():
    # Define test user data
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword",
        "full_name": "Test User"
    }

    # Send POST request to register user
    response = client.post("/register", json=user_data)

    # Assert the response status code
    assert response.status_code == 200

    # Assert response JSON structure
    response_json = response.json()
    assert response_json["username"] == user_data["username"]
    assert response_json["email"] == user_data["email"]
    assert response_json["full_name"] == user_data["full_name"]

def test_register_existing_user():
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword",
        "full_name": "Test User"
    }

    # First registration should succeed
    response = client.post("/register", json=user_data)
    assert response.status_code == 200

    # Second registration should fail (duplicate username)
    response = client.post("/register", json=user_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"
