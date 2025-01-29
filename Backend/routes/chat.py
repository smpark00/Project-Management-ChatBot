# app/routes/chat.py
from fastapi import APIRouter, HTTPException
from services.vectorstore import VectorStoreService
from services.openai_service import OpenAIService

router = APIRouter()
vectorstore_service = VectorStoreService()
openai_service = OpenAIService()

@router.post("/chat")
def chat_endpoint(query: str, model_name: str = "gpt-4o-mini", temperature: float = 0.1, top_p: float = 1.0, k: int = 20):
    try:
        # VectorStore에서 유사 문서 검색
        results = vectorstore_service.similarity_search(query, k=k)
    except KeyError as e:
        print(f"KeyError during similarity_search: {e}")
        return {"error": "문서 검색 중 오류가 발생했습니다."}
    except Exception as e:
        print(f"Unexpected error during similarity_search: {e}")
        return {"error": "문서 검색 중 예상치 못한 오류가 발생했습니다."}

    # 검색 결과의 문서 내용 합치기
    context = ""
    for doc in results:
        doc_id = doc.metadata.get('id', 'Unknown')
        if isinstance(doc_id, (int,)):
            doc_id_str = vectorstore_service.index_to_docstore_id.get(int(doc_id), 'Unknown')
            print(f"문서 ID (변환 전): {doc_id}, 타입: {type(doc_id)}")
            print(f"문서 ID (변환 후): {doc_id_str}, 타입: {type(doc_id_str)}")
            context += f"- {vectorstore_service.get_document_content(doc_id_str)}\n"
        else:
            context += f"- {doc.page_content}\n"

    # OpenAI API 호출
    prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer:"
    answer = openai_service.query_openai(prompt, model_name=model_name, temperature=temperature, top_p=top_p)

    return {"query": query, "response": answer, "context": context}
