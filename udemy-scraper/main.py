"""Get Udemy Course Data:
1 page has roughly 10 courses
proxy is finicky so use with caution 
default: proxy = False (should default to no proxy on faliure, if proxy=True)
APIs are overloaded easily so default delay between requests is 2 s (can be changed to whatever)
"""

import json
from multiprocessing import Process

from scrapers import CoursesityUdemy, RealDiscountUdemy

api1 = CoursesityUdemy(num_pages=10, proxy=False, delay=2)
api2 = RealDiscountUdemy(num_pages=10, proxy=False, delay=2)


def start_1():
    data = api1.gather_udemy_courses()
    with open("udemy1.json", "w") as f:
        json.dump(data, f, indent=2)


def start_2():
    data = api2.gather_udemy_courses()
    with open("udemy2.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    p1 = Process(target=start_1)
    p1.start()
    p2 = Process(target=start_2)
    p2.start()
    p1.join()
    p2.join()
