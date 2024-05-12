import httpx
import orjson


class SyncEmailRequestHandler:
    """
    Class for sending requests to the email service
    """

    def __init__(self, email_service_url: str):
        self.url = email_service_url
        self.client = httpx.Client()
        self.headers = {"Content-Type": "application/json"}

    @staticmethod
    def create_message(user_email: str, subject: str, message: str) -> dict:
        data = {
            "address": user_email,
            "subject": subject,
            "message": message,
        }
        return orjson.dumps(data)

    def push_message(self, data: dict):
        response = self.client.post(self.url, data=data, headers=self.headers)
        response.raise_for_status()

    def create_and_push_message(
        self, user_email: str, subject: str, message: str
    ) -> None:
        data = self.create_message(user_email, subject, message)
        self.push_message(data)

    def close_connection(self):
        self.client.close()
