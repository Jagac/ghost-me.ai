import base64
import json
from urllib.parse import urlparse
from datetime import datetime
import pika
import os

from emailrq import EmailRequestHandler
from llama.ingest import VectorHandler
from llama.llm import LLM


class Consumer:
    def __init__(self, amqp_url: str):
        url_parts = urlparse(amqp_url)

        rabbitmq_params = {
            "host": url_parts.hostname,
            "port": url_parts.port or 5672,
            "virtualhost": url_parts.path[1:] if url_parts.path else "/",
            "login": url_parts.username,
            "password": url_parts.password,
        }

        connection_params = pika.ConnectionParameters(
            host=rabbitmq_params["host"],
            port=rabbitmq_params["port"],
            virtual_host=rabbitmq_params["virtualhost"],
            credentials=pika.PlainCredentials(
                rabbitmq_params["login"], rabbitmq_params["password"]
            ),
        )

        self.connection = pika.BlockingConnection(connection_params)
        self.channel = self.connection.channel()

        self.email_service = EmailRequestHandler(
            email_service_url="http://emailservice:8000/v1/email"
        )

        self.llm = LLM(
            llama_path="model/llama-2-7b-chat.ggmlv3.q8_0.bin",
            embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
        )
        self.qa_bot_instance = self.llm.initialize_rag()

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
            queue="upload_queue", on_message_callback=self.on_message
        )

        print("Waiting for messages")
        self.channel.start_consuming()

    def on_message(self, channel, method_frame, header_frame, body):
        message = json.loads(body.decode())
        username = message.get("username")
        job_desc = message.get("job_desc")

        file_content_base64 = message.get("file_content")
        print(file_content_base64)
        file_content = base64.b64decode(file_content_base64)
        print(file_content)

        pdf_filename = f"{username}.pdf"
        with open(pdf_filename, "wb") as pdf_file:
            pdf_file.write(file_content)

        vector_db = VectorHandler(
            job_desc=job_desc,
            resume_pdf_path=pdf_filename,
            db_connection_string="postgresql://jagac:123@db_postgres/ghostmedb",
            embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
        )

        if vector_db.initialize_vector_db():
            answer = self.llm.answer_query(
                query="Based on the job description, the resume, find the interests and recommend the exact courses you"
                      "know name 3",
                qa_bot_instance=self.qa_bot_instance,
            )
            extracted_answer = answer.get("result").strip()

            self.email_service.create_and_push_message(
                user_email=username,
                subject="Ghostme.ai courses",
                message=extracted_answer,
            )

        else:
            self.email_service.create_and_push_message(
                user_email="jagac41@gmail.com",
                subject="Ghostme.ai down",
                message=f"{datetime.now()} Consumer app is down",
            )

        os.remove(pdf_filename)
        os.remove("job_desc.txt")
        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)


if __name__ == "__main__":
    consumer = Consumer(amqp_url="amqp://guest:guest@rabbitmq:5672")
    consumer.initialize_consumer()
