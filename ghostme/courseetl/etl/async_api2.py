import asyncio
import logging
from typing import Any, Dict

import httpx
import psycopg2
from aiolimiter import AsyncLimiter

logging.basicConfig(level=logging.INFO)
from typing import List

rate_limit = AsyncLimiter(2, 1)


async def make_request(
    client: httpx.AsyncClient,
    url: str,
    rate_limit: AsyncLimiter,
    max_retries=5,
    retry_delay=10,
) -> Dict[str, Any]:
    async with rate_limit:
        for attempt in range(1, max_retries + 1):
            try:
                request = await client.get(url)
                response = request.json()["results"]
                return response

            except httpx.HTTPError as e:
                # Log the error or perform other actions if needed
                logging.info(f"Attempt {attempt} failed with error: {e}")

                # If it's the last attempt, raise the last encountered error
                if attempt == max_retries:
                    raise e

                retry_delay *= 2
                # Log the payload for retry
                logging.info(f"Retrying after {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)


async def extract(base_url):
    urls = [base_url.format(i) for i in range(1, 11)]

    async with httpx.AsyncClient() as client:
        tasks = []
        for url in urls:
            task = make_request(client, url, rate_limit)
            tasks.append(task)

        data = await asyncio.gather(*tasks)

    return data


def transform(data: dict) -> dict:
    json_object = []

    for idx, val in enumerate(data):
        for course in val:
            try:
                new_course = {
                    "id": course["id"],
                    "title": course["name"],
                    "headline": course["shoer_description"],
                    "rating": course["rating"],
                    "enrolled": course["students"],
                    "url": course["url"],
                    "duration": course["lectures"],
                    "section": course["category"],
                    "sub_category": course["subcategory"],
                    "price": course["price"],
                }
            except:
                continue

            json_object.append(new_course)

    return json_object


def dump_to_pgs(
    rds_user: str, rds_password: str, rds_host: str, data: List[dict], table: str
) -> None:
    with psycopg2.connect(
        database="ghostmedb",
        user=rds_user,
        password=rds_password,
        host=rds_host,
        port="5432",
    ) as conn:
        with conn.cursor() as cur:
            # Create the table if it doesn't exist
            create_table_query = """
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                headline TEXT,
                rating FLOAT,
                enrolled INTEGER,
                url TEXT,
                duration VARCHAR(10),
                section VARCHAR(50),
                sub_category VARCHAR(50),
                price VARCHAR(20)
            );
            """
            cur.execute(create_table_query)

            insert_data_query = """
            INSERT INTO courses (id, title, headline, rating, enrolled, url, duration, section, sub_category, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """

            # Iterate over each dictionary in the list of data
            for course_data in data:
                values = (
                    course_data["id"],
                    course_data["title"],
                    course_data["headline"],
                    course_data["rating"],
                    course_data["enrolled"],
                    course_data["url"],
                    course_data["duration"],
                    course_data["section"],
                    course_data["sub_category"],
                    course_data["price"],
                )

                cur.execute(insert_data_query, values)

            conn.commit()


def main():
    base_url = "https://www.real.discount/api-web/all-courses/?store=Udemy&page={}&per_page=10&orderby=undefined&free=0&search=&language=English&cat=&subcat=&editorschoices="
    raw_data = asyncio.run(extract(base_url))
    transformed = transform(raw_data)
    print(transformed)
    # dump_to_pgs("jagac", "123", "db_postgres", transformed, "courses")
