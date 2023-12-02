from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"server": "works"}


def test_create_upload_file():
    files = {"file": ("file.pdf", open("Jagos Perovic_Resume.pdf", "rb"))}
    headers = {"X-API-Key": "test"}
    response = client.post("/uploadfile/", files=files, headers=headers)

    assert response.status_code == 200
    assert response.json() == {"status": "File uploaded successfully"}
