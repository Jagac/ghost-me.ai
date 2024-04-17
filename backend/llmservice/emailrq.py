import httpx
import json


class EmailRequestHandler:
    """
    Class for sending requests to the email service
    """

    def __init__(self, email_service_url: str):
        self.url = email_service_url
        self.client = httpx.Client()

    @staticmethod
    def create_message(user_email: str, subject: str, message: str) -> dict:
        data = {
            "address": user_email,
            "subject": subject,
            "message": message,
        }
        return json.dumps(data)

    def push_message(self, data: dict):
        response = self.client.post(self.url, data=data)
        print(response.json())

    def create_and_push_message(self, user_email, subject, message):
        data = self.create_message(user_email, subject, message)
        self.push_message(data)

    def close_connection(self):
        self.client.close()
