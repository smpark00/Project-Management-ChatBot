from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain import hub
from langchain.schema import Document

# 설정: 벡터 스토어 경로 및 임베딩 모델
VECTOR_STORE_PATH = "./vectorstore"
EMBEDDINGS = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")

# 벡터 스토어 생성 함수
def create_vectorstore():
    # 문서와 메타데이터
    documents = [
        Document(
            page_content="Reacto is a lightweight IDE for React.js developers.",
            metadata={"source": "Reacto Guide", "page": 1}
        ),
        Document(
            page_content="EveningKid is the main contributor to the Reacto project.",
            metadata={"source": "Contributor List", "page": 3}
        ),
    ]
    
    # 벡터 스토어 생성 및 저장
    vectorstore = FAISS.from_documents(documents, EMBEDDINGS)
    vectorstore.save_local(VECTOR_STORE_PATH)
    print("Vector store created and saved.")

# 벡터 스토어 로드
def load_vectorstore():
    return FAISS.load_local(
        VECTOR_STORE_PATH,
        EMBEDDINGS,
        allow_dangerous_deserialization=True
    )

# 문서 포맷팅 함수: 검색된 문서를 LLM에 전달할 형식으로 변환
def format_docs(docs):
    formatted_docs = []
    for doc in docs:
        source = doc.metadata.get("source", "Unknown Source")
        page = doc.metadata.get("page", "Unknown Page")
        formatted_docs.append(f"Source: {source}, Page: {page}\nContent: {doc.page_content}")
    return "\n\n".join(formatted_docs)

# RAG 체인 구성
def build_rag_chain(vectorstore):
    # LLM 설정: Ollama 모델
    llm = ChatOllama(model="llama3.2")

    # Prompt 로드
    prompt = hub.pull("rlm/rag-prompt")

    # 문서 검색 및 컨텍스트 생성
    rag_chain_from_docs = (
        RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
        | prompt
        | llm
        | StrOutputParser()
    )

    # 검색 및 질문 처리 병렬 실행
    rag_chain_with_source = RunnableParallel(
        {"context": vectorstore.as_retriever(), "question": RunnablePassthrough()}
    ).assign(answer=rag_chain_from_docs)

    return rag_chain_with_source

# 벡터 스토어 테스트: 검색 결과 디버깅
def test_vectorstore_search(vectorstore):
    query = "Who is the main contributor of the Reacto project?"
    results = vectorstore.similarity_search(query, k=5)
    
    print("Search Results:")
    if not results:
        print("No documents found.")
    else:
        for i, doc in enumerate(results):
            print(f"Document {i + 1}:\nContent: {doc.page_content}\nMetadata: {doc.metadata}")

# 메인 함수
def main():
    # 벡터 스토어 생성 (필요할 경우 주석 제거)
    # create_vectorstore()
    
    # 벡터 스토어 로드
    vectorstore = load_vectorstore()
    
    # 벡터 스토어 검색 결과 테스트
    test_vectorstore_search(vectorstore)

    # RAG 체인 빌드
    rag_chain_with_source = build_rag_chain(vectorstore)

    # 사용자 입력 질문
    query = "According to data, Who is the most contributor of the Reacto project?"
    
    # RAG 체인을 사용해 응답 생성
    response = rag_chain_with_source.invoke(query)

    # 응답 출력
    print("Answer:\n", response.get("answer", "No answer generated.") + "\n")

    # 소스 문서 출력
    print("Sources:")
    sources = response.get("context", [])
    if not sources:
        print("No relevant sources found for the query.")
    else:
        for i, doc in enumerate(sources):
            print(f"Source {i + 1}:")
            print(f"  Metadata: {doc.metadata}")
            print(f"  Content Preview: {doc.page_content[:200]}")  # 내용 일부만 출력

if __name__ == "__main__":
    main()
