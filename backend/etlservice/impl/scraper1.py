import asyncio
import logging
from typing import Any

import httpx
from aiolimiter import AsyncLimiter

from .base import CourseExtractor
from .database import DatabaseHandler


class CoursesityCourseExtractor(CourseExtractor):
    def __init__(
        self, url: str, db_conn_string: str, payload: dict, rate_limit: AsyncLimiter
    ):
        super().__init__(db_conn_string, rate_limit)
        self.url = url
        self.payload = payload

    async def make_request(
        self, client: httpx.AsyncClient, payload: dict, *args, **kwargs
    ) -> dict[str, Any]:
        """
        Make a request to the api, on error exponential delay and return a dict response
        """
        async with self.rate_limit:
            for attempt in range(1, 2226):
                try:
                    request = await client.post(self.url, json=payload)
                    request.raise_for_status()
                    response = request.json()["data"]["courseData"]
                    return response
                except httpx.HTTPError as e:
                    logging.info(f"Attempt {attempt} failed with error: {e}")
                    if attempt == 5:
                        raise e
                    await asyncio.sleep(2**attempt)

    async def extract_and_dump(self):
        """
        Extraction requires post requests, so we have to specify the payload
        After every 5 requests, clean the data and dump it to PostgreSQL
        """
        payloads = []
        for i in range(1, 20):
            payload2 = self.payload.copy()
            payload2["page"] = i
            payloads.append(payload2)
        async with httpx.AsyncClient() as client:
            tasks = []
            cleaned_data = []
            for idx, payload in enumerate(payloads, start=1):
                task = self.make_request(client=client, payload=payload)
                tasks.append(task)
                if idx % 5 == 0 or idx == len(payloads):
                    raw_data = await asyncio.gather(*tasks)
                    tasks = []
                    transformed_data = self.transform(raw_data)
                    cleaned_data.extend(transformed_data)
                    if cleaned_data:
                        self.db_handler.create_table("courses")
                        self.db_handler.dump_to_pgs(cleaned_data, "courses")
                        logging.info("Added to postgres")
                        cleaned_data = []

    def transform(self, data: tuple[Any]) -> list[dict]:
        """
        Gets only the data we need
        """
        json_object = []
        for val in data:
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

        logging.info("Transformed")
        return json_object
