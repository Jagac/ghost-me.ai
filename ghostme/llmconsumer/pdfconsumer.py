import pika
import json
import base64


def create_rabbitmq_connection():
    rabbitmq_params = {
        "host": "localhost",
        "port": 5672,
        "virtualhost": "/",
        "login": "guest",
        "password": "guest",
    }

    connection_params = pika.ConnectionParameters(
        host=rabbitmq_params["host"],
        port=rabbitmq_params["port"],
        virtual_host=rabbitmq_params["virtualhost"],
        credentials=pika.PlainCredentials(
            rabbitmq_params["login"], rabbitmq_params["password"]
        ),
    )

    connection = pika.BlockingConnection(connection_params)
    return connection


def on_message(channel, method_frame, header_frame, body):
    message = json.loads(body.decode())
    username = message.get("username")
    job_desc = message.get("job_desc")

    # Decode the base64-encoded content back to bytes
    file_content_base64 = message.get("file_content")
    file_content = base64.b64decode(file_content_base64.encode())

    print(f"Received message: {message}")
    print(f"Username: {username}")
    print(f"Job Description: {job_desc}")

    # Write the bytes to a PDF file
    pdf_filename = f"{username}_{job_desc}.pdf"  # Adjust the filename as needed
    with open(pdf_filename, "wb") as pdf_file:
        pdf_file.write(file_content)

    print(f"PDF file '{pdf_filename}' written successfully.")

    channel.basic_ack(delivery_tag=method_frame.delivery_tag)


def create_consumer():
    connection = create_rabbitmq_connection()
    channel = connection.channel()

    # Specify the exchange type when creating the exchange
    channel.exchange_declare(
        exchange="upload_exchange", exchange_type="direct", durable=True
    )

    queue = channel.queue_declare(queue="upload_queue", durable=True)
    channel.queue_bind(
        exchange="upload_exchange", queue="upload_queue", routing_key="resume_pdf"
    )

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="upload_queue", on_message_callback=on_message)

    print("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    create_consumer()
