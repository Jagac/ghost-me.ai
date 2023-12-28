import base64
from typing import Optional

import requests


class GhostWrapper:
    def __init__(
        self,
        email: str,
        password: str,
        registration_key: str,
        local: Optional[bool] = False,
    ):
        if local:
            self.base_url = "http://localhost:8080"
        else:
            self.base_url = "https://ghost-me-api.onrender.com"

        self.user_data = {
            "username": email,
            "password": password,
        }
        self.api_key = registration_key

    def register(self):
        url = self.base_url + "/ghostmev1/users/register"

        headers = {
            "API-Key": self.api_key,
        }

        response = requests.post(url, json=self.user_data, headers=headers)

        if response.status_code == 201:
            print("User created successfully")
        else:
            print(f"Failed to create user. Status code: {response.status_code}")
            print(response.text)

    def get_access_token(self) -> str:
        url = self.base_url + "/ghostmev1/users/login"

        response = requests.post(url, json=self.user_data)
        access_token = response.json()["access_token"]
        if response.status_code == 201:
            print(f"User logged in successfully. Access Token: {access_token}")

        return access_token

    def upload_data(self, jwt_token: str, file_path: str, job_description: str):
        url = self.base_url + "/ghostmev1/uploads"

        headers = {
            "Authorization": f"Bearer {jwt_token}",
        }

        params = {
            "job_desc": job_description,
        }

        files = {
            "file": (
                "file.pdf",
                open(
                    f"{file_path}",
                    "rb",
                ),
                "application/pdf",
            ),
        }

        response = requests.post(url, headers=headers, params=params, files=files)

        if response.status_code == 202:
            print("PDF file upload accepted successfully")
        else:
            print(f"Failed to upload PDF file. Status code: {response.status_code}")
            print(response.text)

    def retrieve_uploaded_data(self, jwt_token: str):
        url = self.base_url + "/ghostmev1/users/uploads"

        headers = {
            "Authorization": f"Bearer {jwt_token}",
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            uploads = response.json()

            for index, upload in enumerate(uploads):
                pdf_resume_base64 = upload.get("pdf_resume", "")
                pdf_resume_content = base64.b64decode(pdf_resume_base64)

                job_description = upload.get("job_description", "")

                file_path = f"downloaded_pdf_{index + 1}.pdf"
                with open(file_path, "wb") as pdf_file:
                    pdf_file.write(pdf_resume_content)

                print(f"Job Description: {job_description}")
                print(f"PDF saved to: {file_path}")

        else:
            print(
                f"Failed to retrieve user uploads. Status code: {response.status_code}"
            )
            print(response.text)

    def delete(self, jwt_token: str):
        url = self.base_url + "/ghostmev1/users/delete"

        headers = {
            "Authorization": f"Bearer {jwt_token}",
        }

        response = requests.delete(url, headers=headers)

        if response.status_code == 200:
            print("User deleted successfully")
        else:
            print(f"Failed to delete user. Status code: {response.status_code}")
            print(response.text)

