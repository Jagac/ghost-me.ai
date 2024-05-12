import logging
import os
from typing import Any, Optional

from langchain.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import CTransformers
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate


class Llm:
    def __init__(self, llama_path: str, embedding_model_name: str) -> None:
        self.prompt_template = """Use the following pieces of context to answer the user's question.
        The example of your response should be:

        Context: {context}
        Question: {question}

        Only return the helpful answer below and nothing else.
        Helpful answer:
        """
        self.llama_path = llama_path
        self.embedding_model = embedding_model_name

    def initialize_rag(
        self, persist_dir: Optional[str] = "./db", device: Optional[str] = "cpu"
    ) -> RetrievalQA:

        embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model,
            model_kwargs={"device": device},
        )

        db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
        llm = self._load_model()
        qa = self._create_retrieval_qa_chain(llm=llm, db=db)

        return qa

    @staticmethod
    def answer_query(query: str, qa_bot_instance: RetrievalQA) -> dict[str, Any]:
        bot_response = qa_bot_instance({"query": query})
        return bot_response

    def _load_model(
        self,
        model_type: Optional[str] = "llama",
        max_new_tokens: Optional[int] = 1024,
        temperature: Optional[float | int] = 0,
    ) -> CTransformers:
        if not os.path.exists(self.llama_path):
            raise FileNotFoundError(f"No model file found at {self.llama_path}")

        llm = CTransformers(
            model=self.llama_path,
            model_type=model_type,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )
        return llm

    def _create_retrieval_qa_chain(self, llm: CTransformers, db: Chroma) -> RetrievalQA:
        qa_prompt = PromptTemplate(
            template=self.prompt_template, input_variables=["context", "question"]
        )
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=db.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": qa_prompt},
        )
        return qa_chain
