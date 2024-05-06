import logging
import os
import shutil

import pika
from emailwrapper.handler import EmailRequestHandler
from llama.llm import LLM
from llama.vectors import VectorHandler

logging.basicConfig(level=logging.INFO)


class Consumer:
    def __init__(self, amqp_url: str, db_conn_string: str) -> None:
        self.connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
        self.channel = self.connection.channel()

        self.email_service = EmailRequestHandler(
            email_service_url="http://emailservice:8000/v1/email"
        )

        self.vector_handler = VectorHandler(
            db_connection_string=db_conn_string,
            embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
        )

        self.llm = LLM(
            llama_path="model/llama-2-7b-chat.ggmlv3.q8_0.bin",
            embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
        )

    def initialize_consumer(self):
        self.channel.exchange_declare(
            exchange="upload_exchange", exchange_type="direct", durable=True
        )
        queue = self.channel.queue_declare(queue="upload_queue", durable=True)
        self.channel.queue_bind(
            exchange="upload_exchange", queue="upload_queue", routing_key="resume_pdf"
        )
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue="upload_queue", on_message_callback=self._on_message
        )
        logging.info("Listening for messages")
        self.channel.start_consuming()

    def _on_message(self, channel, method_frame, header_frame, body) -> None:
        try:
            self.vector_handler.initialize_vector_db(body)
            self.qa_bot_instance = self.llm.initialize_rag()

            answer = self.llm.answer_query(
                query="Based on the job description, the resume, find the "
                "interests and recommend the exact courses you know name 3",
                qa_bot_instance=self.qa_bot_instance,
            )
            extracted_answer = answer.get("result").strip()

            self.email_service.create_and_push_message(
                user_email=self.vector_handler.email,
                subject="Courses",
                message=extracted_answer,
            )
            self.email_service.close_connection()

        except:
            self.email_service.create_and_push_message(
                user_email="jagac41@gmail.com",
                subject="service down",
                message="llm service is down",
            )

        shutil.rmtree("db")
        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)


if __name__ == "__main__":
    consumer = Consumer(os.getenv("MQ_CONN_STRING"), os.getenv("DB_CONN_STRING"))
    consumer.initialize_consumer()
