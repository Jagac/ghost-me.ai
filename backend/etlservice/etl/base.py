import abc
import asyncio
import logging
from typing import Any

import httpx
from aiolimiter import AsyncLimiter

from .database import DatabaseHandler


class CourseExtractor(abc.ABC):
    def __init__(self, db_conn_string: str, rate_limit: AsyncLimiter):
        self.db_handler = DatabaseHandler(db_conn_string)
        self.rate_limit = rate_limit
        self.logging_config()

    def logging_config(self):
        logging.basicConfig(level=logging.INFO)

    @abc.abstractmethod
    async def make_request(
        self, client: httpx.AsyncClient, *args, **kwargs
    ) -> dict[str, Any]:
        pass

    @abc.abstractmethod
    async def extract_and_dump(self):
        pass

    @abc.abstractmethod
    def transform(self, data: tuple[Any]) -> list[dict]:
        pass

    def run(self):
        asyncio.run(self.extract_and_dump())
