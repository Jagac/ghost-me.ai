import asyncio
import logging
from typing import Any

import httpx
from aiolimiter import AsyncLimiter

from .database import DatabaseHandler


class CoursesityCourseExtractor:
    def __init__(
        self, url: str, db_conn_string: str, payload: dict, rate_limit: AsyncLimiter
    ):
        self.url = url
        self.payload = payload
        self.db_handler = DatabaseHandler(db_conn_string)
        self.rate_limit = rate_limit
        self.logging_config()

    def logging_config(self):
        logging.basicConfig(level=logging.INFO)

    async def make_request(
        self,
        client: httpx.AsyncClient,
        payload: dict,
        limit: AsyncLimiter,
        max_retries=5,
        retry_delay=10,
    ) -> dict[str, Any]:
        """
        Make a request to the api, on error exponential delay and return a dict response
        Args:
            client: client for httpx
            payload: parameters for httpx to send to api
            limit: rate limit as the api can crash
            max_retries: number of times to retry on failure
            retry_delay: starting delay (exponentially increases)

        Returns:

        """
        async with limit:
            for attempt in range(1, max_retries + 1):
                try:
                    request = await client.post(self.url, json=payload)
                    request.raise_for_status()
                    response = request.json()["data"]["courseData"]
                    return response
                except httpx.HTTPError as e:
                    logging.info(f"Attempt {attempt} failed with error: {e}")

                    if attempt == max_retries:
                        raise e

                    retry_delay *= 2
                    logging.info(f"Retrying after {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)

    async def extract(self) -> tuple[Any]:
        """
        Extraction requires post requests, so we have to specify the payload
        Returns: extracted data

        """
        payloads = []
        for i in range(1, 20):
            payload2 = self.payload.copy()
            payload2["page"] = i
            payloads.append(payload2)

        async with httpx.AsyncClient() as client:
            tasks = []

            for payload in payloads:
                task = self.make_request(
                    client=client, payload=payload, limit=self.rate_limit
                )
                tasks.append(task)

            data = await asyncio.gather(*tasks)

        return data

    @staticmethod
    def transform(data: tuple[Any]) -> list[dict]:
        """
        Gets only the data we need
        Args:
            data: extracted data using the extract() function

        Returns: cleaned data

        """
        json_object = []
        for idx, val in enumerate(data):
            for course_info in val:
                course = {
                    "id": course_info.get("productId", None),
                    "title": course_info.get("title", None),
                    "headline": course_info.get("headline", None),
                    "rating": course_info.get("avgRating", None),
                    "enrolled": course_info.get("totalEnrollment", None),
                    "url": course_info.get("url", None),
                    "duration": course_info.get("durationHours", None),
                    "section": course_info.get("courseSection", None),
                    "sub_category": course_info.get("subCategory", None),
                    "price": course_info.get("priceType", None),
                }

                json_object.append(course)

        return json_object

    def run(self):
        raw_data = asyncio.run(self.extract())
        transformed = self.transform(raw_data)

        self.db_handler.create_table("courses")
        self.db_handler.dump_to_pgs(transformed, "courses")
