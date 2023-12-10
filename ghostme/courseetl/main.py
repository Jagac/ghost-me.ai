import asyncio
import schedule
import time
import logging
from etl import async_api1, async_api2

logging.basicConfig(level=logging.INFO)


def job_task1():
    logging.info("Task 1 started")
    async_api1.main()


def job_task2():
    logging.info("Task 2 started")
    async_api2.main()


def main():
    time.sleep(10)
    logging.info("Initial run of tasks")
    job_task1()
    job_task2()
    schedule.every().hour.at(":00").do(job_task1)
    schedule.every().hour.at(":00").do(job_task2)

    while True:
        schedule.run_pending()
        time.sleep(1)


main()
