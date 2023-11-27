import json

import pika
import polars as pl
import base64
from secrets import token_hex


class MQProducer:
    def __init__(self, queue_name) -> None:
        self.connection_params = pika.ConnectionParameters("localhost", heartbeat=0)
        self.connection = pika.BlockingConnection(self.connection_params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue_name)

    def publish(self, message, routing_key):
        self.channel.basic_publish(exchange="", routing_key=routing_key, body=message)


class MQConsumer:
    def __init__(self, queue_name) -> None:
        self.queue_name = queue_name
        self.connection_params = pika.ConnectionParameters("localhost", heartbeat=0)
        self.connection = pika.BlockingConnection(self.connection_params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name)

    def on_msg_received(self, ch, method, properties, body):
        df1 = pl.DataFrame()

        file = json.loads(body)
        for i in file:
            print(i)

    def pdf(self, ch, method, properties, body):
        bytes = base64.b64decode(body)
        file_name = token_hex(10)
        with open(f"{file_name}.pdf", "wb") as f:
            f.write(bytes)
            f.close()

    def consume_json(self):
        self.channel.basic_consume(
            queue=self.queue_name,
            auto_ack=True,
            on_message_callback=self.on_msg_received,
        )
        self.channel.start_consuming()

    def consume_pdf(self):
        self.channel.basic_consume(
            queue=self.queue_name,
            auto_ack=True,
            on_message_callback=self.pdf,
        )
        self.channel.start_consuming()
