import re

from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import HuggingFaceInstructEmbeddings

from langchain.text_splitter import RecursiveCharacterTextSplitter


class LLM:
    def __init__(self, file: str) -> None:
        self.file = file

    def load(self):
        pdf_loader = PyPDFLoader(
            self.file,
        )
        pdf_pages = pdf_loader.load()

        return pdf_pages

    def chunk(self, chunk_size=2000):
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", " ", ""],
            chunk_size=chunk_size,
            chunk_overlap=512,
        )
        chunks = text_splitter.split_documents(self.load())
        docs_text = [doc.page_content for doc in chunks]
        docs_text = [re.sub("[^a-zA-Z0-9 \n\.]", " ", doc) for doc in docs_text]
        docs_text = [doc.replace("\n", "") for doc in docs_text]

        return docs_text

    def embed(self, text):
        model_name = "hkunlp/instructor-large"

        hf_embeddings = HuggingFaceInstructEmbeddings(model_name=model_name)

        query_result = hf_embeddings.embed_documents(text)

        return query_result
