"""Get Udemy Course Data:
1 page has roughly 10 courses
proxy is finicky so use with caution 
default: proxy = False (should default to no proxy on faliure, if proxy=True)
APIs are overloaded easily so default delay between requests is 2 s (can be changed to whatever)
"""

import argparse
import json
from multiprocessing import Process

from scrapers import CoursesityUdemy, RealDiscountUdemy

parser = argparse.ArgumentParser(description="script settings")
parser.add_argument(
    "--num_pages",
    metavar="num_pages",
    type=int,
    help="1 page has roughly 10 courses",
    default=10,
)
parser.add_argument(
    "--proxy",
    metavar="proxy",
    type=bool,
    help="chose wether you want a proxy",
    default=False,
)
parser.add_argument(
    "--delay",
    metavar="delay",
    type=float,
    help="wait between requests(seconds)",
    default=2,
)

args = parser.parse_args()
num_pages = args.num_pages
proxy = args.proxy
delay = args.delay

api1 = CoursesityUdemy(num_pages=num_pages, proxy=proxy, delay=delay)
api2 = RealDiscountUdemy(num_pages=num_pages, proxy=proxy, delay=delay)


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
