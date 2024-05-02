import abc
from .database import DatabaseHandler
from aiolimiter import AsyncLimiter
import logging
import httpx
from typing import Any
import asyncio


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
