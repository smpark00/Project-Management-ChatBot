import os
import json
import openai
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

# 환경 변수 로드
load_dotenv()

# 모델 설정
model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = SentenceTransformerEmbeddings(model_name=model_name)

# ✅ vectorstore 경로 (vector_service.py에서 만든 벡터스토어 경로와 일치해야 함)
vectorstore_dir = "./storage/Algorithm/vectorstore"  # 경로를 적절히 변경하세요

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

# ✅ FastAPI 앱 & APIRouter 초기화
app = FastAPI()
router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.1
    top_p: float = 1.0
    k: int = 20


def query_openai(
    prompt: str, model_name: str = "gpt-4o-mini", temperature=0.1, top_p=1.0
) -> str:
    """
    OpenAI API를 호출하여 답변을 생성
    """
    try:
        client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Provide answers based on given context.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            top_p=top_p,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error querying OpenAI: {e}")
        return "죄송합니다. 응답 생성 중 오류가 발생했습니다."


@router.post("/chat")
def chat(request: ChatRequest):
    """
    유사도 검색을 수행한 후 OpenAI API를 호출하여 응답을 반환
    """
    query = request.query
    model_name = request.model_name
    temperature = request.temperature
    top_p = request.top_p
    k = request.k

    # ✅ FAISS VectorStore에서 유사 문서 검색
    try:
        search_results = vectorstore.similarity_search(query, k=k)
    except KeyError as e:
        print(f"KeyError during similarity_search: {e}")
        print(f"문서 ID 타입: {type(e.args[0])}, 값: {e.args[0]}")
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
            print(f"문서 ID (변환 전): {doc_id}, 타입: {type(doc_id)}")
            print(f"문서 ID (변환 후): {doc_id_str}, 타입: {type(doc_id_str)}")

            if doc_id_str in docstore:
                context += f"- {docstore.get(doc_id_str).page_content}\n"
            else:
                print(f"⚠️ docstore.json에서 찾을 수 없음: {doc_id_str}")
        else:
            context += f"- {doc.page_content}\n"

    # ✅ OpenAI API 호출
    prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer:"
    answer = query_openai(
        prompt, model_name=model_name, temperature=temperature, top_p=top_p
    )

    return {"query": query, "response": answer, "context": context}


# ✅ FastAPI 앱에 `router` 추가
app.include_router(router)

# ✅ FastAPI 실행 (uvicorn 사용)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
