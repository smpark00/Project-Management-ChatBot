import os
import json
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
import numpy as np

import faiss
from langchain.schema import Document
from langchain.docstore.in_memory import InMemoryDocstore
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS as LangchainFAISS

# OpenAI API 서비스 불러오기
from services.openai_service import OpenAIService

# 환경 변수 로드
load_dotenv()

# ✅ OpenAIService 인스턴스 생성
openai_service = OpenAIService()

# 모델 설정
model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = SentenceTransformerEmbeddings(model_name=model_name)

# ✅ FastAPI 앱 & APIRouter 초기화
app = FastAPI()
router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    project_name: str  # ✅ 프론트에서 프로젝트명을 입력받도록 추가
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.1
    top_p: float = 1.0
    k: int = 20


def load_vectorstore(project_name: str):
    """
    동적으로 프로젝트별 FAISS 벡터스토어를 로드하는 함수
    """
    # ✅ 프로젝트에 맞는 벡터스토어 경로 설정
    vectorstore_dir = f"./storage/{project_name}/vectorstore"

    # ✅ FAISS 인덱스 로드
    faiss_index_path = os.path.join(vectorstore_dir, "index.faiss")
    if not os.path.isfile(faiss_index_path):
        raise FileNotFoundError(f"FAISS index file not found at: {faiss_index_path}")
    faiss_index = faiss.read_index(faiss_index_path)

    # ✅ `docstore.json` 로드
    docstore_path = os.path.join(vectorstore_dir, "docstore.json")
    if not os.path.isfile(docstore_path):
        raise FileNotFoundError(f"docstore.json file not found at: {docstore_path}")
    with open(docstore_path, "r", encoding="utf-8") as f:
        doc_dict = json.load(f)

    # ✅ 문서 객체 변환 (`docstore.json` -> InMemoryDocstore)
    reconstructed_docstore = {
        str(k): Document(page_content=v["page_content"], metadata={"id": str(k)})
        for k, v in doc_dict.items()
    }
    docstore = InMemoryDocstore(reconstructed_docstore)

    # ✅ `index_to_docstore_id.json` 로드 및 정수형 변환
    mapping_path = os.path.join(vectorstore_dir, "index_to_docstore_id.json")
    if not os.path.isfile(mapping_path):
        raise FileNotFoundError(
            f"index_to_docstore_id.json file not found at: {mapping_path}"
        )
    with open(mapping_path, "r", encoding="utf-8") as f:
        index_to_docstore_id_raw = json.load(f)
    index_to_docstore_id = {int(k): str(v) for k, v in index_to_docstore_id_raw.items()}

    # ✅ Langchain FAISS VectorStore 생성
    vectorstore = LangchainFAISS(
        embedding_function=embeddings,
        index=faiss_index,
        docstore=docstore,
        index_to_docstore_id=index_to_docstore_id,
    )

    return vectorstore, docstore, index_to_docstore_id


@router.post("/chat")
def chat(request: ChatRequest):
    """
    유사도 검색을 수행한 후 OpenAI API를 호출하여 응답을 반환
    """
    query = request.query
    project_name = request.project_name
    model_name = request.model_name
    temperature = request.temperature
    top_p = request.top_p
    k = request.k

    try:
        # ✅ 프로젝트별 벡터스토어 로드
        vectorstore, docstore, index_to_docstore_id = load_vectorstore(project_name)

        # ✅ FAISS VectorStore에서 유사 문서 검색
        search_results = vectorstore.similarity_search(query, k=k)

    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
        return {
            "error": f"프로젝트 '{project_name}'의 벡터 데이터베이스가 존재하지 않습니다."
        }
    except KeyError as e:
        print(f"KeyError during similarity_search: {e}")
        return {"error": "문서 검색 중 오류가 발생했습니다."}
    except Exception as e:
        print(f"Unexpected error during similarity_search: {e}")
        return {"error": "문서 검색 중 예상치 못한 오류가 발생했습니다."}

    # ✅ 검색된 문서들의 ID 변환 및 컨텍스트 생성
    context = ""
    for doc in search_results:
        doc_id = doc.metadata.get("id", "Unknown")
        if isinstance(doc_id, (int, np.integer)):
            # ✅ ID 변환 (index_to_docstore_id 사용)
            doc_id_str = index_to_docstore_id.get(int(doc_id), "Unknown")
            if doc_id_str in docstore:
                context += f"- {docstore.get(doc_id_str).page_content}\n"
            else:
                print(f"⚠️ docstore.json에서 찾을 수 없음: {doc_id_str}")
        else:
            context += f"- {doc.page_content}\n"

    # ✅ OpenAI API 호출 (openai_service.py 활용)
    prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer:"
    answer = openai_service.query_openai(
        prompt, model_name=model_name, temperature=temperature, top_p=top_p
    )

    return {"query": query, "response": answer, "context": context}
