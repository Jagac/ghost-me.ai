import httpx
import json
import time
from tqdm import tqdm
from fp.fp import FreeProxy
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def generate_payloads(payload: dict, num_pages: int) -> list[dict]:
    # make payloads to request different pages
    # we care about page number, everything else can stay the same
    lst = []
    for i in range(1, num_pages + 1):
        payload2 = payload.copy()
        payload2["page"] = i
        lst.append(payload2)

    return lst


def make_request(client: httpx.Client, url: str, payload: dict) -> json:
    # simple request
    request = client.post(url, json=payload)
    response = request.json()

    return response


def parse(payload_list: list[dict], url: str, proxy: FreeProxy) -> dict:
    # used to only extract course data from the api
    with httpx.Client(proxies=proxy) as client:
        data = []
        for payload in tqdm(payload_list):
            response = make_request(client, url, payload)
            data.append(response["data"])
            time.sleep(2)

    return data


def cleanup(data: dict) -> dict:
    # extracts only the necessary data
    json_object = []
    for idx, val in enumerate(data):
        course_data = data[idx]["courseData"]

        for course_info in course_data:
            course = {
                "id": course_info["productId"],
                "title": course_info["title"],
                "headline": course_info["headline"],
                "total_rating": course_info["totalRating"],
                "avg_rating": course_info["avgRating"],
                "enrolled": course_info["totalEnrollment"],
                "url": course_info["url"],
                "duration": course_info["durationHours"],
                "section": course_info["courseSection"],
                "sub_category": course_info["subCategory"],
                "url_slug": course_info["urlSlug"],
                "section_slug": course_info["courseSectionUrlslug"],
                "prce": course_info["priceType"],
            }

            json_object.append(course)

    return json_object


def main():
    url = "https://api.coursesity.com/api/courses/"  # hidden api
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
    prox = FreeProxy(rand=False, timeout=1)
    logging.info(prox)
    payload_list = generate_payloads(payload=payload, num_pages=10)
    data = parse(payload_list=payload_list, url=url, proxy=prox.get())
    cleaned_data = cleanup(data=data)

    print(cleaned_data)


if __name__ == "__main__":
    main()
