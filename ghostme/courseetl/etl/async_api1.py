import asyncio
from typing import Any, Dict, List
import httpx
from aiolimiter import AsyncLimiter
import psycopg2
from psycopg2.extras import execute_values

rate_limit = AsyncLimiter(2, 2)


async def make_request(
    client: httpx.AsyncClient,
    url: str,
    payload: dict,
    rate_limit,
    max_retries=3,
    retry_delay=10,
) -> Dict[str, Any]:
    async with rate_limit:
        for attempt in range(1, max_retries + 1):
            try:
                request = await client.post(url, json=payload)
                request.raise_for_status()  # Raise HTTPError for bad responses
                response = request.json()["data"]["courseData"]
                return response
            except httpx.HTTPError as e:
                # Log the error or perform other actions if needed
                print(f"Attempt {attempt} failed with error: {e}")

                # If it's the last attempt, raise the last encountered error
                if attempt == max_retries:
                    raise e

                # Log the payload for retry
                print(f"Retrying after {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)


async def extract(starting_payload, url):
    payloads = []
    for i in range(1, 10):
        payload2 = starting_payload.copy()
        payload2["page"] = i
        payloads.append(payload2)

    async with httpx.AsyncClient() as client:
        tasks = []

        for payload in payloads:
            task = make_request(client, url, payload, rate_limit)
            tasks.append(task)

        data = await asyncio.gather(*tasks)

    return data


def transform(data: List[dict]) -> List[dict]:
    # extracts only the necessary data
    json_object = []
    for idx, val in enumerate(data):
        for course_info in val:
            course = {
                "id": course_info["productId"],
                "title": course_info["title"],
                "headline": course_info["headline"],
                "rating": course_info["avgRating"],
                "enrolled": course_info["totalEnrollment"],
                "url": course_info["url"],
                "duration": course_info["durationHours"],
                "section": course_info["courseSection"],
                "sub_category": course_info["subCategory"],
                "prce": course_info["priceType"],
            }

            json_object.append(course)

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
                    course_data["prce"],
                )

                cur.execute(insert_data_query, values)

            conn.commit()


def main():
    url = "https://api.coursesity.com/api/courses/"
    payload = {
        "page": 1,
        "limit": 10,
        "sort_by": "best-online-courses",
        "course_type": "",
        "provider": "",
        "order_by": "desc",
        "category_value": "",
        "topic_value": "",
        "language_value": "",
        "price_value": "",
        "section_value": "",
    }

    raw_data = asyncio.run(extract(payload, url))
    transformed = transform(raw_data)
    dump_to_pgs("jagac", "123", "db_postgres", transformed, "courses")
