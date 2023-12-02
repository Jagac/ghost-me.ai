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
import time
from multiprocessing import Process

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))
from mq import MQProducer
from scrapers import CoursesityUdemy, RealDiscountUdemy

# parser = argparse.ArgumentParser(description="script settings")
# parser.add_argument(
#     "--num_pages",
#     metavar="num_pages",
#     type=int,
#     help="1 page has roughly 10 courses",
#     default=10,
# )
# parser.add_argument(
#     "--proxy",
#     metavar="proxy",
#     type=bool,
#     help="chose wether you want a proxy",
#     default=False,
# )
# parser.add_argument(
#     "--delay",
#     metavar="delay",
#     type=float,
#     help="wait between requests(seconds)",
#     default=2,
# )

# args = parser.parse_args()

api1 = CoursesityUdemy()
api2 = RealDiscountUdemy()


def start_1(api=api1):
    data = api.gather_udemy_courses()
    producer1 = MQProducer(queue_name="udemy_courses_1")
    chunkSize = 5
    for i in range(0, len(data) + chunkSize, chunkSize):
        producer1.publish(
            message=json.dumps(data[i : i + chunkSize]), routing_key="udemy_courses_1"
        )
        time.sleep(0.5)


def start_2(api=api2):
    data = api.gather_udemy_courses()
    producer2 = MQProducer(queue_name="udemy_courses_2")
    chunkSize = 5
    for i in range(0, len(data) + chunkSize, chunkSize):
        producer2.publish(
            message=json.dumps(data[i : i + chunkSize]), routing_key="udemy_courses_2"
        )
        time.sleep(1)


from fastapi import (BackgroundTasks, Depends, FastAPI, File, HTTPException,
                     status)
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
app = FastAPI()


def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key is None or api_key != "test":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key


@app.get("/")
async def main():
    return {"server": "works"}


@app.post("/trigger-task/{data}")
async def trigger_task(
    data: str, background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)
):
    background_tasks.add_task(start_1)
    background_tasks.add_task(start_2)

    return {"message": "task triggered"}


# if __name__ == "__main__":
#     p1 = Process(target=start_1)
#     p1.start()
#     p2 = Process(target=start_2)
#     p2.start()
#     p1.join()
#     p2.join()
