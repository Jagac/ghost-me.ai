import asyncio
import logging
from typing import Any

import httpx
from aiolimiter import AsyncLimiter

from .database import DatabaseHandler


class RealDiscountCourseExtractor:
    def __init__(self, base_url: str, db_conn_string: str, rate_limit: AsyncLimiter):
        self.base_url = base_url
        self.db_handler = DatabaseHandler(db_conn_string)
        self.logging_config()
        self.rate_limit = rate_limit

    def logging_config(self):
        logging.basicConfig(level=logging.INFO)

    @staticmethod
    async def make_request(
        client: httpx.AsyncClient,
        url: str,
        limit: AsyncLimiter,
        max_retries=5,
        retry_delay=10,
    ) -> dict[str, Any]:
        """
         Make a request to the api, on error exponential delay and return a dict response
        Args:
            client: httpx client to use
            url: api url to request
            limit: rate limit
            max_retries: number of times to retry
            retry_delay: delay between

        Returns:

        """
        async with limit:
            for attempt in range(1, max_retries + 1):
                try:
                    request = await client.get(url)
                    response = request.json()["results"]
                    return response

                except httpx.HTTPError as e:
                    logging.info(f"Attempt {attempt} failed with error: {e}")

                    if attempt == max_retries:
                        raise e

                    retry_delay *= 2
                    # Log the payload for retry
                    logging.info(f"Retrying after {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)

    async def extract(self) -> tuple[Any]:
        """
        Extraction requires post requests, so we have to specify the payload
        Returns: extracted data

        """
        urls = [self.base_url.format(i) for i in range(1, 20)]

        async with httpx.AsyncClient() as client:
            tasks = []
            for url in urls:
                task = self.make_request(client, url, self.rate_limit)
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
            for course in val:
                new_course = {
                    "id": course.get("id", None),
                    "title": course.get("name", None),
                    "headline": course.get("shoer_description", None),
                    "rating": course.get("rating", None),
                    "enrolled": course.get("students", None),
                    "url": course.get("url", None),
                    "duration": course.get("lectures", None),
                    "section": course.get("category", None),
                    "sub_category": course.get("subcategory", None),
                    "price": course.get("price", None),
                }

                json_object.append(new_course)

        return json_object

    def run(self):
        raw_data = asyncio.run(self.extract())
        transformed = self.transform(raw_data)

        self.db_handler.create_table("courses")
        self.db_handler.dump_to_pgs(transformed, "courses")
