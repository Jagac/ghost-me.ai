import logging
import pika
import io
import PyPDF2
from langchain.docstore.document import Document


class MQConsumer:
    def __init__(self, queue_name: str) -> None:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger()

        self.queue_name = queue_name
        self.connection_params = pika.ConnectionParameters("localhost", heartbeat=0)
        self.connection = pika.BlockingConnection(self.connection_params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name)


class PDFConsumer(MQConsumer):
    def __init__(self, queue_name: str) -> None:
        super().__init__(queue_name)

    def pdf(self, ch, method, properties, body):
        pdf_stream = io.BytesIO(body)
        pdf_reader = PyPDF2.PdfReader(pdf_stream)
        resume_text = str()
        for page in pdf_reader.pages:
            resume_text += page.extract_text()

        docs = Document(page_content=resume_text)
        print(docs)

    def consume_pdf(self):
        self.channel.basic_consume(
            queue=self.queue_name,
            auto_ack=True,
            on_message_callback=self.pdf,
        )
        self.channel.start_consuming()


conns = PDFConsumer("resume_pdf")
conns.consume_pdf()
