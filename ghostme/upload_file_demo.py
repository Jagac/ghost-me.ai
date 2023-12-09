# demo on how to interact with the api using requests
import requests

# ============================================#
api_url = "http://localhost:8080"
user_registration_data = {"username": "jagac", "password": "jagac"}
user_login_data = {"username": "jagac", "password": "jagac"}
file_path = "/home/jagac/ghost-me.ai/ghostme/pdfproducer/Jagos Perovic_Resume.pdf"
# ============================================#


# sign up and log in to obtain a jwt token (expires after 30 min)
def register_user():
    response = requests.post(f"{api_url}/users/register", json=user_registration_data)
    response.raise_for_status()
    print("User registration response:", response.text)


def get_token():
    response = requests.post(f"{api_url}/users/login", json=user_login_data)
    response.raise_for_status()
    token_data = response.json()
    print("Login response:", token_data)

    return token_data


# use the token to access the upload endpoint and upload a pdf
def send_upload_file_request(jwt_token):
    files = {"file": ("file.pdf", open(file_path, "rb"), "application/pdf")}
    headers = {"Authorization": f"Bearer {jwt_token}"}
    params = {"job_desc": "testing job_desc"}  # Include job_desc in query parameters

    response = requests.post(
        f"{api_url}/uploadfile/", files=files, headers=headers, params=params
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")


def main():
    register_user()
    token_data = get_token()
    jwt_token = token_data.get("access_token", "")

    send_upload_file_request(jwt_token)


if __name__ == "__main__":
    main()
