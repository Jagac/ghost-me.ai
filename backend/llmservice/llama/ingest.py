import os

import pandas as pd
import psycopg2
from langchain.document_loaders import DataFrameLoader, PyPDFLoader, TextLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.vectorstores.utils import filter_complex_metadata

ABS_PATH = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(ABS_PATH, "db")


class VectorHandler:
    def __init__(
        self,
        job_desc: str,
        resume_pdf_path: str,
        db_connection_string: str,
        embedding_model_name: str,
    ) -> None:
        self.job_desc = job_desc
        self.resume_pdf_path = resume_pdf_path
        self.db_connection_string = db_connection_string
        self.embedding_model_name = embedding_model_name

    def _load_job_description(self) -> list:
        with open("job_desc.txt", "w") as f:
            f.write(self.job_desc)
        loaded_desc = TextLoader("job_desc.txt")
        return loaded_desc.load()

    def _load_resume_documents(self) -> list:
        loaded_documents = PyPDFLoader(self.resume_pdf_path)
        return loaded_documents.load()

    def _load_course_titles_from_db(self) -> list:
        with psycopg2.connect(self.db_connection_string) as connection:
            query = "SELECT title FROM courses"
            df = pd.read_sql_query(query, connection)
        df = df.rename(columns={"title": "text"})
        loaded_df = DataFrameLoader(df, page_content_column="text")
        return loaded_df.load()

    def initialize_vector_db(self):
        loaded_desc = self._load_job_description()
        loaded_documents = self._load_resume_documents()
        loaded_df = self._load_course_titles_from_db()

        all_loaders = [loaded_df, loaded_documents, loaded_desc]
        loaded_documents = [document for loader in all_loaders for document in loader]

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

        return True
