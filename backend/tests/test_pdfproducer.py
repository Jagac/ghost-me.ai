from fastapi.testclient import TestClient

# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.dirname(CURRENT_DIR))
from ghostme.api.main import app

client = TestClient(app)


def test_create_user():
    response = client.post(
        "/ghostmev1/users/register",
        json={"username": "testuser", "password": "testpassword"},
    )
    assert response.status_code == 201
    assert response.json() == {"message": "User created successfully"}


def test_create_user_invalid_input():
    response = client.post("/ghostmev1/users/register", json={})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_login_user():
    response = client.post(
        "/ghostmev1/users/login",
        json={"username": "testuser", "password": "testpassword"},
    )
    assert response.status_code == 201
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_user_invalid_credentials():
    response = client.post(
        "/ghostmev1/users/login",
        json={"username": "nonexistent", "password": "wrongpassword"},
    )
    assert response.status_code == 401  # 401 Unauthorized
    assert "detail" in response.json()
    assert response.json()["detail"] == "Invalid username or password"


def test_create_upload_file():
    response = client.post(
        "/ghostmev1/uploads",
        data={"job_desc": "Test Job"},
        files={"file": ("test.pdf", b"dummy content", "application/pdf")},
    )
    assert response.status_code == 202
    assert response.json() == {"message": "Data uploaded successfully"}


def test_create_upload_file_missing_file():
    response = client.post("/ghostmev1/uploads", data={"job_desc": "Test Job"})
    assert response.status_code == 400  # 400 Bad Request
    assert "detail" in response.json()
    assert response.json()["detail"] == "No file provided"


def test_get_user_uploads():
    response = client.get("/ghostmev1/users/uploads")
    assert response.status_code == 200
    # Add more assertions based on the expected response structure


def test_get_user_uploads_user_not_found():
    response = client.get(
        "/ghostmev1/users/uploads", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401  # 401 Unauthorized
    assert "detail" in response.json()


def test_delete_user():
    response = client.delete("/ghostmev1/users/delete")
    assert response.status_code == 200
    assert response.json() == {
        "message": "User and associated data deleted successfully"
    }


def test_delete_user_not_found():
    response = client.delete(
        "/ghostmev1/users/delete", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401  # 401 Unauthorized
    assert "detail" in response.json()
