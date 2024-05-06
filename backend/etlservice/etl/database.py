import json
from urllib.parse import urlparse

import psycopg2


class DatabaseHandler:
    def __init__(self, conn_string: str):
        self.conn_string = urlparse(conn_string)

        self.db_username = self.conn_string.username
        self.db_password = self.conn_string.password
        self.db_host = self.conn_string.hostname
        self.db_port = self.conn_string.port
        self.db_name = self.conn_string.path[1:]

    def create_table(self, table: str) -> None:
        """
        Create table if not exists
        Args:
            table: postgres table name

        Returns: None

        """
        with psycopg2.connect(
            dbname=self.db_name,
            user=self.db_username,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id INTEGER,
                    title VARCHAR(255) NOT NULL,
                    headline TEXT,
                    rating FLOAT,
                    enrolled INTEGER,
                    url TEXT,
                    duration VARCHAR(10),
                    section VARCHAR(50),
                    sub_category VARCHAR(50),
                    price VARCHAR(20)
                );
                """
                )

    def dump_to_pgs(self, data: list[dict], table: str) -> None:
        """
        Dumps json data to PostgreSQL
        Args:
            data: list of dictionaries to dump to PostgreSQL
            table: postgres table name

        Returns: None

        """
        with psycopg2.connect(
            dbname=self.db_name,
            user=self.db_username,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
        ) as conn:
            with conn.cursor() as cur:
                query_sql = f""" insert into {table}
                               select * from json_populate_recordset(NULL::{table}, %s) """
                cur.execute(query_sql, (json.dumps(data),))
