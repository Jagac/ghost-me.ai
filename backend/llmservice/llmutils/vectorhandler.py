import base64
import json
import os

import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.utils import filter_complex_metadata
from langchain_community.document_loaders import (DataFrameLoader, PyPDFLoader,
                                                  TextLoader)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from sqlalchemy import create_engine

ABS_PATH = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(ABS_PATH, "db")


class VectorHandler:
    def __init__(
        self,
        db_conn_string: str,
        embedding_model_name: str,
    ) -> None:
        self.engine = create_engine(db_conn_string)
        self.embedding_model_name = embedding_model_name

    def _extract_from_sources(self, body: bytes) -> list[str, str, pd.DataFrame]:
        message = json.loads(body.decode())
        email = message.get("email")
        job_desc = message.get("job_desc")

        job_desc_filename = f"{email}_job_desc.txt"
        with open(job_desc_filename, "w") as job_desc_file:
            job_desc_file.write(job_desc)

        file_content_base64 = message.get("file_content")
        file_content = base64.b64decode(file_content_base64)

        pdf_filename = f"{email}.pdf"
        with open(pdf_filename, "wb") as pdf_file:
            pdf_file.write(file_content)

        query = "SELECT title, headline FROM courses"
        df = pd.read_sql_query(query, self.engine)
        df["text"] = df["title"] + "" + df["headline"]

        return job_desc_filename, pdf_filename, df, email

    def initialize_vectors_for_user(self, body: bytes):
        job_desc_filename, pdf_filename, df, email = self._extract_from_sources(body)

        loaded_desc = TextLoader(job_desc_filename)
        loaded_documents = PyPDFLoader(pdf_filename)
        loaded_df = DataFrameLoader(df, page_content_column="text")

        all_loaders = [loaded_df, loaded_documents, loaded_desc]
        loaded_documents = [
            document for loader in all_loaders for document in loader.load()
        ]

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=64)
        chunked_documents = text_splitter.split_documents(loaded_documents)

        huggingface_embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name,
            model_kwargs={"device": "cpu"},
        )

        documents = filter_complex_metadata(chunked_documents)
        vector_database = Chroma.from_documents(
            documents=documents,
            embedding=huggingface_embeddings,
            persist_directory=DB_DIR,
        )

        vector_database.persist()

        os.remove(job_desc_filename)
        os.remove(pdf_filename)

        return email
