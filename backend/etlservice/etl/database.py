import json

import psycopg2


class DatabaseHandler:
    def __init__(self, conn_string: str):
        self.conn_string = conn_string

    def create_table(self, table: str) -> None:
        """
        Create table if not exists
        Args:
            table: postgres table name

        Returns: None

        """
        with psycopg2.connect(self.conn_string) as conn:
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
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor() as cur:
                query_sql = f""" insert into {table}
                               select * from json_populate_recordset(NULL::{table}, %s) """
                cur.execute(query_sql, (json.dumps(data),))
