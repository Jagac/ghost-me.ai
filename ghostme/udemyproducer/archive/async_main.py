# not usable as it overloads the API
import asyncio
import json

import httpx

url = "https://api.coursesity.com/api/courses/"  # hidden api

# used by website to display data
# we care about page number, everything else can stay the same
payload = {
    "page": 1,
    "limit": 10,
    "sort_by": "",
    "course_type": "free",
    "provider": "udemy-courses",
    "order_by": "desc",
    "category_value": "",
    "topic_value": "",
    "language_value": "",
    "price_value": "",
    "section_value": "",
}

# make payloads to request different pages
lst = []
for i in range(1, 10):
    payload2 = payload.copy()
    payload2["page"] = i
    lst.append(payload2)


async def make_request(client: httpx.AsyncClient, url: str, payload: dict) -> json:
    request = await client.post(url, json=payload)
    response = request.json()
    return response


async def main():
    async with httpx.AsyncClient() as client:
        tasks = []
        for payload in lst:
            tasks.append(asyncio.ensure_future(make_request(client, url, payload)))

        data = await asyncio.gather(*tasks)
        for i in data:
            print(i["data"])


if __name__ == "__main__":
    asyncio.run(main())
