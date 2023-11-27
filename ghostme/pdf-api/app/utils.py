import json

import pika
import polars as pl


class MQProducer:
    def __init__(self, queue_name) -> None:
        self.connection_params = pika.ConnectionParameters("localhost", heartbeat=0)
        self.connection = pika.BlockingConnection(self.connection_params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue_name)

    def publish(self, message, routing_key):
        self.channel.basic_publish(exchange="", routing_key=routing_key, body=message)