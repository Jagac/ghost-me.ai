import logging
import pika
import io
import PyPDF2
from langchain.docstore.document import Document

import aio_pika
import asyncio


async def setup_rabbitmq_connection():
    rabbitmq_params = {
        "host": "localhost",  # Replace with your RabbitMQ container name or IP
        "port": 5672,
        "virtualhost": "/",
        "login": "guest",
        "password": "guest",
    }

    connection = await aio_pika.connect_robust(
        f"amqp://{rabbitmq_params['login']}:{rabbitmq_params['password']}@{rabbitmq_params['host']}:{rabbitmq_params['port']}/{rabbitmq_params['virtualhost']}"
    )

    return connection


async def consume_messages(channel, exchange, queue):
    async def on_message(message: aio_pika.IncomingMessage):
        async with message.process():
            body = message.body
            pdf_stream = io.BytesIO(body)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            resume_text = str()
            for page in pdf_reader.pages:
                resume_text += page.extract_text()
            # Process the message (replace this with your own logic)
            print(f"Received message: {resume_text.strip()}")

    await queue.bind(exchange, routing_key="resume_pdf")
    await queue.consume(on_message)


async def main():
    rabbitmq_connection = await setup_rabbitmq_connection()
    channel = await rabbitmq_connection.channel()
    exchange = await channel.declare_exchange(
        "upload_exchange", type="direct", durable=True
    )
    queue = await channel.declare_queue("upload_queue", durable=True)

    # Start consuming messages in a separate coroutine
    asyncio.create_task(consume_messages(channel, exchange, queue))

    # Keep the main coroutine running indefinitely
    try:
        while True:
            await asyncio.sleep(2)  # Sleep for 1 hour (adjust as needed)
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup and close the connection when the program is interrupted
        await rabbitmq_connection.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
