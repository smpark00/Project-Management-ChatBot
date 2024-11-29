from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain import hub

# 설정: 벡터 스토어 및 LLM 모델
VECTOR_STORE_PATH = "./vectorstore"

# Hugging Face 임베딩 모델 사용
from langchain_huggingface import HuggingFaceEmbeddings
EMBEDDINGS = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")

# 벡터 스토어 로드
vectorstore = FAISS.load_local(
    VECTOR_STORE_PATH,
    EMBEDDINGS,
    allow_dangerous_deserialization=True
)

from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3.2")

# Prompt 로드
prompt = hub.pull("rlm/rag-prompt")

# 문서 포맷팅 함수
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# RAG 체인 구성
retriever = vectorstore.as_retriever()

# RAG 체인: 문서를 LLM의 컨텍스트로 전달
rag_chain_from_docs = (
    RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
    | prompt
    | llm
    | StrOutputParser()
)

# RAG 체인: 문서 검색과 질문 처리를 병렬로 수행
rag_chain_with_source = RunnableParallel(
    {"context": retriever, "question": RunnablePassthrough()}
).assign(answer=rag_chain_from_docs)

def main():
    # 사용자 입력 질문
    query = "Who is the most contributor of the Reacto project?"
    
    # RAG 체인을 사용해 응답 생성
    response = rag_chain_with_source.invoke(query)

    # 응답 출력
    print("Answer:\n", response.get("answer", "No answer generated.") + "\n")

    # 소스 문서 출력
    print("Sources:")
    sources = response.get("context", [])
    
    # 검색된 문서가 없을 경우 처리
    if not sources:
        print("No relevant sources found for the query.")
    else:
        for i, source in enumerate(sources):
            print(f"Source {i + 1}: {source.metadata}")


if __name__ == "__main__":
    main()

