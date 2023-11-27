"""Get Udemy Course Data:
1 page has roughly 10 courses
proxy is finicky so use with caution 
default: proxy = False (should default to no proxy on faliure, if proxy=True)
APIs are overloaded easily so default delay between requests is 2 s (can be changed to whatever)
"""

import argparse
import json
import os
import sys
from multiprocessing import Process

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))
from rabbit.mq import MQProducer

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
    producer1 = MQProducer(queue_name="udemy_courses_1")
    chunkSize = 5
    for i in range(0, len(data) + chunkSize, chunkSize):
        producer1.publish(
            message=json.dumps(data[i : i + chunkSize]), routing_key="udemy_courses_1"
        )


def start_2():
    data = api2.gather_udemy_courses()
    producer2 = MQProducer(queue_name="udemy_courses_2")
    chunkSize = 5
    for i in range(0, len(data) + chunkSize, chunkSize):
        producer2.publish(
            message=json.dumps(data[i : i + chunkSize]), routing_key="udemy_courses_2"
        )


if __name__ == "__main__":
    p1 = Process(target=start_1)
    p1.start()
    p2 = Process(target=start_2)
    p2.start()
    p1.join()
    p2.join()
