# https://aio-pika.readthedocs.io/en/latest/rabbitmq-tutorial/2-work-queues.html
import aio_pika


class MQ:
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
        file_content: bytes, rabbitmq_connection: aio_pika.robust_connection
    ) -> None:
        channel = await rabbitmq_connection.channel()
        exchange = await channel.declare_exchange(
            "upload_exchange", type="direct", durable=True
        )
        queue = await channel.declare_queue("upload_queue", durable=True)
        await queue.bind(exchange, routing_key="resume_pdf")

        message_body = file_content
        await exchange.publish(
            aio_pika.Message(
                body=message_body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key="resume_pdf",
        )
