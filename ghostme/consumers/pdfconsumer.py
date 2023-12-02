import base64
import os
import sys
from secrets import token_hex

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))

from rabbit.mq import MQConsumer


class PDFConsumer(MQConsumer):
    def __init__(self, queue_name) -> None:
        super().__init__(queue_name)

    def pdf(self, ch, method, properties, body):
        file_name = token_hex(10)
        with open(f"{file_name}.pdf", "wb") as f:
            f.write(body)
            f.close()

        self.logger.info(f"received {file_name}")
        # os.remove(f"{file_name}.pdf")

    def consume_pdf(self):
        self.channel.basic_consume(
            queue=self.queue_name,
            auto_ack=True,
            on_message_callback=self.pdf,
        )
        self.channel.start_consuming()


conns = PDFConsumer("resume_pdf")
conns.consume_pdf()
