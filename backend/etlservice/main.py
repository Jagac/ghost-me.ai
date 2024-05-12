import os
from multiprocessing import Process

from aiolimiter import AsyncLimiter
from impl.scraper1 import CoursesityCourseExtractor
from impl.scraper2 import RealDiscountCourseExtractor

db_conn_string = os.getenv("DB_CONN_STRING")
rate_limit = AsyncLimiter(max_rate=2, time_period=1)


def run_course1():
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
    url = "https://api.coursesity.com/api/courses/"
    course1 = CoursesityCourseExtractor(
        url=url, db_conn_string=db_conn_string, payload=payload, rate_limit=rate_limit
    )
    course1.run()


def run_course2():
    base_url = (
        "https://www.real.discount/api-web/all-courses/?store=Udemy&page={"
        "}&per_page=10&orderby=undefined&free=0&search=&language=English&cat=&subcat=&editorschoices="
    )
    course2 = RealDiscountCourseExtractor(
        base_url=base_url, db_conn_string=db_conn_string, rate_limit=rate_limit
    )
    course2.run()


if __name__ == "__main__":
    process1 = Process(target=run_course1)
    process2 = Process(target=run_course2)

    process2.start()
    process1.start()

    process2.join()
    process1.join()
