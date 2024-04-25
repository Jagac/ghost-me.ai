import asyncio
import json

import httpx


class EmailRequestHandler:
    """
    Class for sending requests to the email service
    """

    def __init__(self, email_service_url: str) -> None:
        self.url = email_service_url
        self.client = httpx.AsyncClient()
        self.headers = {"Content-Type": "application/json"}

    @staticmethod
    def create_message(user_email: str, subject: str, message: str) -> dict[str]:

        data = {
            "address": user_email,
            "subject": subject,
            "message": message,
        }
        return json.dumps(data)

    async def push_message(self, data: dict):
        async with self.client as client:
            response = await client.post(self.url, data=data, headers=self.headers)
            response.raise_for_status()
            print(response.status_code)

    async def create_and_push_message(
        self, user_email: str, subject: str, message: str
    ) -> None:
        data = self.create_message(user_email, subject, message)
        await self.push_message(data)

    async def close_connection(self):
        await self.client.aclose()
