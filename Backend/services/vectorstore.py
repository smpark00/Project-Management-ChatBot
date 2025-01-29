# app/services/vectorstore.py
import os
import json
import faiss
from langchain.schema import Document
from langchain.docstore.in_memory import InMemoryDocstore
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS as LangchainFAISS
from config import settings

class VectorStoreService:
    def __init__(self):
        self.embeddings = SentenceTransformerEmbeddings(model_name=settings.MODEL_NAME)
        self.vectorstore_dir = settings.VECTORSTORE_DIR

        # FAISS 인덱스 로드
        faiss_index_path = os.path.join(self.vectorstore_dir, "index.faiss")
        if not os.path.isfile(faiss_index_path):
            raise FileNotFoundError(f"FAISS index file not found at: {faiss_index_path}")
        self.faiss_index = faiss.read_index(faiss_index_path)
        print("FAISS 인덱스 로드 완료")

        # docstore.json 로드
        docstore_path = os.path.join(self.vectorstore_dir, "docstore.json")
        if not os.path.isfile(docstore_path):
            raise FileNotFoundError(f"docstore.json 파일을 찾을 수 없습니다: {docstore_path}")
        with open(docstore_path, "r", encoding="utf-8") as f:
            doc_dict = json.load(f)

        # Document 객체로 변환
        reconstructed_docstore = {
            str(k): Document(page_content=v['page_content'], metadata={"id": str(k)})
            for k, v in doc_dict.items()
        }
        self.docstore = InMemoryDocstore(reconstructed_docstore)

        # index_to_docstore_id.json 로드
        mapping_path = os.path.join(self.vectorstore_dir, "index_to_docstore_id.json")
        if not os.path.isfile(mapping_path):
            raise FileNotFoundError(f"index_to_docstore_id.json 파일을 찾을 수 없습니다: {mapping_path}")
        with open(mapping_path, "r", encoding="utf-8") as f:
            index_to_docstore_id_raw = json.load(f)
        self.index_to_docstore_id = {int(k): str(v) for k, v in index_to_docstore_id_raw.items()}

        # VectorStore 생성
        self.vectorstore = LangchainFAISS(
            embedding_function=self.embeddings,
            index=self.faiss_index,
            docstore=self.docstore,
            index_to_docstore_id=self.index_to_docstore_id
        )
        print("VectorStore 생성 완료")

    def similarity_search(self, query: str, k: int):
        return self.vectorstore.similarity_search(query, k=k)

    def get_document_content(self, doc_id):
        return self.docstore.get(doc_id).page_content
