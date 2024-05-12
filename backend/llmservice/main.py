import os

from consumer import Consumer


def main():
    llm = os.getenv("LLM")
    consumer = Consumer(
        amqp_url=os.getenv("MQ_CONN_STRING"),
        db_conn_string=os.getenv("DB_CONN_STRING"),
        email_service_url="http://emailservice:8000/v1/email",
        llama_path=f"model/{llm}",
        embedding_model_name=os.getenv("EMBEDDING_MODEL"),
    )
    while True:
        consumer.initialize_consumer()


if __name__ == "__main__":
    main()
