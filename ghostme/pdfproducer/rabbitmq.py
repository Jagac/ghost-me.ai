# https://aio-pika.readthedocs.io/en/latest/rabbitmq-tutorial/2-work-queues.html
import aio_pika
import json
import base64

async def create_rabbitmq_connection() -> aio_pika.robust_connection:
    rabbitmq_params = {
        "host": "rabbitmq",
        "port": 5672,
        "virtualhost": "/",
        "login": "guest",
        "password": "guest",
    }

    connection = await aio_pika.connect_robust(
        f"amqp://{rabbitmq_params['login']}:{rabbitmq_params['password']}@{rabbitmq_params['host']}:{rabbitmq_params['port']}/{rabbitmq_params['virtualhost']}"
    )

    return connection


async def publish_message(
    file_content: bytes,
    job_desc: str,
    username: str,
    rabbitmq_connection: aio_pika.robust_connection,
) -> None:
    channel = await rabbitmq_connection.channel()
    exchange = await channel.declare_exchange(
        "upload_exchange", type="direct", durable=True
    )
    queue = await channel.declare_queue("upload_queue", durable=True)
    await queue.bind(exchange, routing_key="resume_pdf")

    file_content_base64 = base64.b64encode(file_content).decode()
    
    message_body = {
        "username": username,
        "file_content": file_content_base64,
        "job_desc": job_desc,
    }
    
    json_message = json.dumps(message_body, ensure_ascii=False).encode("utf-8")
    
    await exchange.publish(
        aio_pika.Message(
            body=json_message,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key="resume_pdf",
    )
