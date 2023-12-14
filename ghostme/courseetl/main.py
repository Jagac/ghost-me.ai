import asyncio
import time
import logging
from etl import async_api1, async_api2

logging.basicConfig(level=logging.INFO)


def main():
    async_api1.main()


if __name__ == "__main__":
    main()
