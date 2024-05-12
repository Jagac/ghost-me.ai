import logging
import os
import shutil

import pika
from emailutils import SyncEmailRequestHandler
from llmutils import Llm, VectorHandler

logging.basicConfig(level=logging.INFO)


class Consumer:
    def __init__(
        self,
        amqp_url: str,
        db_conn_string: str,
        email_service_url: str,
        llama_path: str,
        embedding_model_name: str,
    ) -> None:
        self.connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
        self.channel = self.connection.channel()

        self.email_service = SyncEmailRequestHandler(email_service_url)
        self.vector_handler = VectorHandler(
            db_conn_string=db_conn_string, embedding_model_name=embedding_model_name
        )
        self.llm = Llm(llama_path=llama_path, embedding_model_name=embedding_model_name)

    def initialize_consumer(self) -> None:
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
            logging.info("Processing request")
            email = self.vector_handler.initialize_vectors_for_user(body)
            qa_bot_instance = self.llm.initialize_rag()

            answer = self.llm.answer_query(
                query="Based on the job description, the resume, find the interests and recommend the exact courses you know name 3",
                qa_bot_instance=qa_bot_instance,
            )
            extracted_answer = answer.get("result").strip()

            self.email_service.create_and_push_message(
                user_email=email, subject="Courses", message=extracted_answer
            )

            logging.info(extracted_answer)

        except FileNotFoundError as e:
            self._handle_error(
                email="jagac41@gmail.com", subject="Service Error", message=str(e)
            )

        except Exception as e:
            self._handle_error(
                email="jagac41@gmail.com", subject="Service Error", message=str(e)
            )

        finally:
            shutil.rmtree("llmutils/db")
            self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def _handle_error(self, email: str, subject: str, message: str) -> None:
        error_message = f"Error occurred: {message}"
        logging.error(error_message)
        self.email_service.create_and_push_message(
            user_email=email, subject=subject, message=error_message
        )
