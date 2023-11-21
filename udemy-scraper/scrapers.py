import logging
import time

import httpx
from fp.fp import FreeProxy

from utils import Super


class CoursesityUdemy(Super):
    def __init__(
        self,
        num_pages: int,
        delay: int | float = 2,
        proxy: bool = False,
    ) -> None:
        super().__init__(num_pages, proxy)

        self.payload = {
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
        self.url = "https://api.coursesity.com/api/courses/"
        self.delay = delay

    def parse(
        self, payload_list: list[dict], url: str, proxy: FreeProxy = None
    ) -> dict:
        # used to only extract course data from the api
        with httpx.Client(proxies=proxy) as client:
            data = []
            for payload in payload_list:
                logging.info(f"page number: {payload['page']}")
                response = self.make_post_request(client, url, payload)
                data.append(response["data"])
                time.sleep(self.delay)

        return data

    def cleanup(self, data: dict) -> dict:
        # extracts only the necessary data
        json_object = []
        for idx, val in enumerate(data):
            course_data = data[idx]["courseData"]

            for course_info in course_data:
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

    def gather_udemy_courses(self) -> dict:
        if self.proxy:
            logging.info("proxy set to True")
            try:
                proxy = self.generate_proxy()
                payload_list = self.generate_payloads()
                data = self.parse(payload_list=payload_list, url=self.url, proxy=proxy)
                cleaned_data = self.cleanup(data=data)

                return cleaned_data

            except:
                logging.exception("error making requests... retry or set proxy = False")

        else:
            payload_list = self.generate_payloads()
            data = self.parse(payload_list=payload_list, url=self.url)
            cleaned_data = self.cleanup(data=data)

            return cleaned_data


class RealDiscountUdemy(Super):
    def __init__(
        self, num_pages: int, proxy: bool = False, delay: int | float = 2
    ) -> None:
        super().__init__(num_pages, proxy)
        self.delay = delay

    def parse(self, url: str, proxy: FreeProxy = None) -> dict:
        # used to only extract course data from the api
        with httpx.Client(proxies=proxy) as client:
            data = self.make_get_request(url=url, client=client)

        return data

    def cleanup(self, data: dict) -> dict:
        json_object = []

        for idx, val in enumerate(data["results"]):
            try:
                course = {
                    "id": val["id"],
                    "title": val["name"],
                    "headline": val["shoer_description"],
                    "rating": val["rating"],
                    "enrolled": val["students"],
                    "url": val["url"],
                    "duration": val["lectures"],
                    "section": val["category"],
                    "sub_category": val["subcategory"],
                    "price": val["price"],
                }
            except:
                continue

            json_object.append(course)

        return json_object

    def gather_udemy_courses(self):
        json_data = []
        if self.proxy:
            proxy = self.generate_proxy()
            try:
                for i in range(1, self.num_pages + 1):
                    logging.info(f"page number: {i}")
                    url = f"https://www.real.discount/api-web/all-courses/?store=Udemy&page={i}&per_page=10&orderby=undefined&free=0&search=&language=English&cat=&subcat=&editorschoices="
                    data = self.parse(url=url, proxy=proxy)
                    cleaned_data = self.cleanup(data=data)

                    json_data.extend(cleaned_data)
                    time.sleep(self.delay)
            except:
                logging.exception("error making requests... retry or set proxy = False")

        else:
            for i in range(1, self.num_pages + 1):
                logging.info(f"page number: {i}")
                url = f"https://www.real.discount/api-web/all-courses/?store=Udemy&page={i}&per_page=10&orderby=undefined&free=0&search=&language=English&cat=&subcat=&editorschoices="
                data = self.parse(url=url)
                cleaned_data = self.cleanup(data=data)

                json_data.extend(cleaned_data)
                time.sleep(self.delay)

        return json_data
