import base64
import json

import aio_pika
from aio_pika.robust_connection import AbstractRobustConnection


class QueueHandler:
    """
    RabbitMQ Service Class
    publishes a json message to RabbitMQ containing the username, job description, and resume pdf.
    The idea is to have competing llm consumers on the other side that will take care of emailing
    """

    def __init__(
        self, connection_url: str, exchange_name: str, queue_name: str, routing_key: str
    ):
        self.connection_url = connection_url
        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.routing_key = routing_key

    async def create_connection(self) -> AbstractRobustConnection:
        connection = await aio_pika.connect_robust(self.connection_url)
        return connection

    async def publish_message(
        self,
        file_content: bytes,
        job_desc: str,
        username: str,
        connection: AbstractRobustConnection,
    ) -> None:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            self.exchange_name, type="direct", durable=True
        )
        queue = await channel.declare_queue(self.queue_name, durable=True)
        await queue.bind(exchange, routing_key=self.routing_key)

        file_content_base64 = base64.b64encode(file_content).decode()

        message_body = {
            "username": username,
            "file_content": file_content_base64,
            "job_desc": job_desc,
        }

        json_message = json.dumps(message_body).encode("utf-8")

        await exchange.publish(
            aio_pika.Message(
                body=json_message,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=self.routing_key,
        )
