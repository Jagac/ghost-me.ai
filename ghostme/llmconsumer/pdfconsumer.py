import asyncio
import io
import logging

import aio_pika
import PyPDF2
from langchain.docstore.document import Document
import aiofiles


async def setup_rabbitmq_connection():
    rabbitmq_params = {
        "host": "rabbitmq",  # Replace with your RabbitMQ container name or IP
        "port": 5672,
        "virtualhost": "/",
        "login": "guest",
        "password": "guest",
    }

    connection = await aio_pika.connect_robust(
        f"amqp://{rabbitmq_params['login']}:{rabbitmq_params['password']}@{rabbitmq_params['host']}:{rabbitmq_params['port']}/{rabbitmq_params['virtualhost']}"
    )
    logging.info("Connected to rabbitmq")
    return connection


async def consume_messages(channel, exchange, queue, ack_event):
    # Set basic.qos to limit the number of unacknowledged messages
    await channel.set_qos(prefetch_count=1)

    async def on_message(message: aio_pika.IncomingMessage):
        try:
            async with message.process():
                body = message.body
                # Process the message (replace this with your own logic)
                print(f"Received message: {body}")

                await message.ack()
        except Exception as e:
            # Handle exceptions during message processing
            logging.error(f"Error processing message: {e}")
            # Do not acknowledge the message to allow for retry or further investigation

        finally:
            # Set the ack_event to notify that the message has been processed
            ack_event.set()

    await queue.bind(exchange, routing_key="resume_pdf")
    await queue.consume(on_message)


async def main():
    ack_event = asyncio.Event()

    rabbitmq_connection = await setup_rabbitmq_connection()
    channel = await rabbitmq_connection.channel()

    exchange = await channel.declare_exchange(
        "upload_exchange", type="direct", durable=True
    )

    queue = await channel.declare_queue("upload_queue", durable=True)
    asyncio.create_task(consume_messages(channel, exchange, queue, ack_event))

    try:
        await ack_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        await rabbitmq_connection.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
