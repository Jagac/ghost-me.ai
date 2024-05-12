import asyncio
import logging
from typing import Any

import httpx
from aiolimiter import AsyncLimiter

from .base import CourseExtractor
from .database import DatabaseHandler


class RealDiscountCourseExtractor(CourseExtractor):
    def __init__(self, base_url: str, db_conn_string: str, rate_limit: AsyncLimiter):
        super().__init__(db_conn_string, rate_limit)
        self.base_url = base_url

    async def make_request(
        self, client: httpx.AsyncClient, url: str, *args, **kwargs
    ) -> dict[str, Any]:
        """
        Make a request to the api, on error exponential delay and return a dict response
        """
        async with self.rate_limit:
            for attempt in range(1, 2520):
                try:
                    request = await client.get(url)
                    request.raise_for_status()
                    response = request.json()["results"]
                    return response
                except httpx.HTTPError as e:
                    logging.info(f"Attempt {attempt} failed with error: {e}")
                    if attempt == 5:
                        raise e
                    await asyncio.sleep(2**attempt)

    async def extract_and_dump(self):
        """
        Extraction requires get requests, so we have to specify the URLs
        After every 5 requests, clean the data and dump it to PostgreSQL
        """
        urls = [self.base_url.format(i) for i in range(1, 2520)]
        async with httpx.AsyncClient() as client:
            tasks = []
            cleaned_data = []
            for idx, url in enumerate(urls, start=1):
                task = self.make_request(client, url)
                tasks.append(task)
                if idx % 5 == 0 or idx == len(urls):
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
            for course in val:
                new_course = {
                    "id": course.get("id", None),
                    "title": course.get("name", None),
                    "headline": course.get("short_description", None),
                    "rating": course.get("rating", None),
                    "enrolled": course.get("students", None),
                    "url": course.get("url", None),
                    "duration": course.get("lectures", None),
                    "section": course.get("category", None),
                    "sub_category": course.get("subcategory", None),
                    "price": course.get("price", None),
                }
                json_object.append(new_course)

        logging.info("Transformed")
        return json_object
