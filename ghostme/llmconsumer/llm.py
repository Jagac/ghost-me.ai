import os
import time

from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import (Docx2txtLoader, PyPDFLoader,
                                        TextLoader, UnstructuredPDFLoader,
                                        YoutubeLoader)
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone


def load_document(file: str) -> str:
    """
    Load a document from a file.

    Parameters:
    file (str): The path to the file.

    Returns:
    str: The loaded document data.

    Raises:
    ValueError: If the document format is not supported.
    """

    # get the name and extension of file
    file_name, extension = os.path.splitext(file)

    if extension == ".pdf":
        # If the file is a PDF, create a PyPDFLoader and load the file
        print(f"Loading {file}")
        loader = UnstructuredPDFLoader(file)
    elif extension == ".docx":
        # If the file is a DOCX, create a Docx2txtLoader and load the file
        print(f"Loading {file}")
        loader = Docx2txtLoader(file)
    elif extension == ".txt":
        # If the file is a TXT, create a TextLoader and load the file
        loader = TextLoader(file)
    else:
        # If the file format is not supported, print an error message and return None
        print("Document format is not supported!")
        return None

    # Load the document using the loader
    data = loader.load_and_split()
    print(len(data))

    return data


def chunk_data(data: str, chunk_size=2000) -> str:
    """
    Chunk the data into smaller pieces.

    Parameters:
    data (str): The data to be chunked.
    chunk_size (int): The desired size of each chunk. Defaults to 256.

    Returns:
    list[str]: The list of chunks.
    """

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=512
    )
    chunks = text_splitter.split_documents(data)

    return chunks
