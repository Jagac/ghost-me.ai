import asyncio
from typing import Any, Dict
import httpx
from aiolimiter import AsyncLimiter
import psycopg2
from psycopg2.extras import execute_values

rate_limit = AsyncLimiter(2, 2)


async def make_request(
    client: httpx.AsyncClient, url: str, rate_limit: AsyncLimiter
) -> Dict[str, Any]:
    async with rate_limit:
        request = await client.get(url)
        response = request.json()["results"]
        return response


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




def main():
    base_url = "https://www.real.discount/api-web/all-courses/?store=Udemy&page={}&per_page=10&orderby=undefined&free=0&search=&language=English&cat=&subcat=&editorschoices="
    raw_data = asyncio.run(extract(base_url))
    transformed = transform(raw_data)
    print(transformed)

    



