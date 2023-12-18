import requests
import base64

base_url = "http://localhost:8080"
user_data = {
    "username": "jagac",
    "password": "jagac",
}


def register_user():
    url = base_url + "/ghostmev1/users/register"
    api_key = "test-user-registration"

    # Example user data

    headers = {
        "API-Key": api_key,
    }

    response = requests.post(url, json=user_data, headers=headers)

    if response.status_code == 201:
        print("User created successfully")
    else:
        print(f"Failed to create user. Status code: {response.status_code}")
        print(response.text)


def login():
    url = base_url + "/ghostmev1/users/login"

    response = requests.post(url, json=user_data)
    access_token = response.json()["access_token"]
    if response.status_code == 201:
        print(f"User logged in successfully. Access Token: {access_token}")

    return access_token


def upload(jwt_token):
    url = base_url + "/ghostmev1/uploads"

    # Example job description and PDF file
    job_desc = "example_job_description"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
    }

    params = {
        "job_desc": job_desc,
    }

    files = {
        "file": (
            "file.pdf",
            open(
                r"C:\Users\Jagos\Documents\GitHub\ghost-me.ai\ghostme\Tina_Huang_Resume_i.pdf",
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


def retrieve_and_save_pdf(jwt_token):
    url = base_url + "/ghostmev1/users/uploads"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        uploads = response.json()
        print("User uploads:")

        for index, upload in enumerate(uploads):
            pdf_resume_content_base64 = upload.get("pdf_resume_content_base64", "")
            pdf_resume_content = base64.b64decode(pdf_resume_content_base64)

            job_description = upload.get("job_description", "")

            # Save the PDF content to a file
            file_path = f"downloaded_pdf_{index + 1}.pdf"
            with open(file_path, "wb") as pdf_file:
                pdf_file.write(pdf_resume_content)

            print(f"Job Description: {job_description}")
            print(f"PDF saved to: {file_path}")
            print()

    else:
        print(f"Failed to retrieve user uploads. Status code: {response.status_code}")
        print(response.text)


def delete(jwt_token):
    url = base_url + "/ghostmev1/users/delete"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
    }

    response = requests.delete(url, headers=headers)

    if response.status_code == 200:
        print("User deleted successfully")
    else:
        print(f"Failed to delete user. Status code: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    register_user()
    jwt_token = login()
    upload(jwt_token)
    retrieve_and_save_pdf(jwt_token)
    delete(jwt_token)
    retrieve_and_save_pdf(jwt_token)
