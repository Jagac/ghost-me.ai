"""Utilities class for interacting with rabbitmq
"""
import logging

import pika


class MQProducer:
    def __init__(self, queue_name: str) -> None:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger()
        self.connection_params = pika.ConnectionParameters(
            host="rabbitmq", port=5672, heartbeat=0
        )
        self.connection = pika.BlockingConnection(self.connection_params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue_name)

    def publish(self, message: bytes | str, routing_key: str):
        self.channel.basic_publish(exchange="", routing_key=routing_key, body=message)


class MQConsumer:
    def __init__(self, queue_name: str) -> None:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger()

        self.queue_name = queue_name
        self.connection_params = pika.ConnectionParameters("localhost", heartbeat=0)
        self.connection = pika.BlockingConnection(self.connection_params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name)
