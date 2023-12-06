# demo on how to interact with the api using requests
import requests

# ============================================#
api_url = "http://localhost:8080"
user_registration_data = {"username": "example_user", "password": "example_password"}
user_login_data = {"username": "example_user", "password": "example_password"}
file_path = "/home/jagac/ghostme/Jagos Perovic_Resume.pdf"
# ============================================#


# sign up and log in to obtain a jwt token (expires after 30 min)
def register_user():
    response = requests.post(f"{api_url}/users/", json=user_registration_data)
    response.raise_for_status()
    print("User registration response:", response.text)


def get_token():
    response = requests.post(f"{api_url}/login/", json=user_login_data)
    response.raise_for_status()
    token_data = response.json()
    print("Login response:", token_data)

    return token_data


# use the token to access the upload endpoint and upload a pdf
def send_upload_file_request(jwt_token):
    files = {"file": ("file.pdf", open(file_path, "rb"), "application/pdf")}
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = requests.post(f"{api_url}/uploadfile/", files=files, headers=headers)

    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")


def main():
    # register_user()
    token_data = get_token()
    jwt_token = token_data.get("access_token", "")

    send_upload_file_request(jwt_token)


if __name__ == "__main__":
    main()
