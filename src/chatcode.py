import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from fastapi import FastAPI
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# HuggingFace Embeddings 설정
EMBEDDINGS = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")

# FastAPI 앱 생성
app = FastAPI()

# 벡터 데이터베이스 로드
def load_vectorstores(base_dir):
    """
    모든 프로젝트의 벡터 데이터베이스 로드
    Args:
        base_dir (str): 벡터 데이터베이스 디렉토리
    Returns:
        dict: 프로젝트 이름별 벡터 데이터베이스
    """
    vectorstores = {}
    for project_name in os.listdir(base_dir):
        project_path = os.path.join(base_dir, project_name)
        if os.path.isdir(project_path):
            vectorstore = FAISS.load_local(project_path, EMBEDDINGS, allow_dangerous_deserialization=True)
            vectorstores[project_name] = vectorstore
    return vectorstores

VECTORSTORES = load_vectorstores("../Github_dataset/vectorstores")

# 질문 벡터화
def embed_query(query):
    """
    질문을 벡터화
    Args:
        query (str): 사용자 질문
    Returns:
        list: 임베딩된 벡터
    """
    query_embedding = EMBEDDINGS.embed_query(query)
    return query_embedding

# 병렬 검색
def search_vectorstores(query, vectorstores, k=5):
    """
    벡터 데이터베이스에서 병렬로 검색
    Args:
        query (str): 사용자 질문
        vectorstores (dict): 프로젝트 이름별 벡터 데이터베이스
        k (int): 반환할 검색 결과 수
    Returns:
        dict: 프로젝트 이름별 검색 결과
    """
    query_embedding = embed_query(query)

    def search_project(project_name, vectorstore):
        results = vectorstore.similarity_search_by_vector(query_embedding, k=k)
        return {project_name: results}

    results = {}
    with ThreadPoolExecutor() as executor:
        future_to_project = {executor.submit(search_project, name, store): name for name, store in vectorstores.items()}
        for future in future_to_project:
            project_name = future_to_project[future]
            try:
                results.update(future.result())
            except Exception as e:
                print(f"Error searching {project_name}: {e}")

    return results

# 검색 결과 병합
def merge_results(search_results):
    """
    검색 결과를 병합하여 Ollama 모델 입력에 적합한 문맥 생성
    Args:
        search_results (dict): 프로젝트별 검색 결과
    Returns:
        str: 병합된 문맥
    """
    context = ""
    for project_name, results in search_results.items():
        context += f"\n## Project: {project_name}\n"
        for doc in results:
            context += f"- {doc.page_content}\n"
    return context

def query_ollama(prompt, model_name="llama3.2"):
    try:
        result = subprocess.run(
            ["ollama", "run", model_name],
            input=prompt,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )
        if result.stderr:
            print(f"Ollama error: {result.stderr}")
        return result.stdout.strip()
    except Exception as e:
        print(f"Error querying Ollama: {e}")
        return "죄송합니다. 응답 생성 중 오류가 발생했습니다."


# Ollama 응답 생성
def generate_response(query, context, model_name="llama3.2"):
    """
    검색 결과와 질문을 기반으로 Ollama 모델에서 응답 생성
    Args:
        query (str): 사용자 질문
        context (str): 검색된 문맥
        model_name (str): Ollama 모델 이름
    Returns:
        str: 모델 응답
    """
    prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer:"
    response = query_ollama(prompt, model_name=model_name)
    return response

# FastAPI 엔드포인트
@app.post("/chat")
def chat(query: str, model_name: str = "llama3.2"):
    """
    사용자 질문을 처리하고 Ollama 모델에서 응답 생성
    Args:
        query (str): 사용자 질문
        model_name (str): Ollama 모델 이름
    Returns:
        dict: 질문, 응답, 검색된 문맥
    """
    search_results = search_vectorstores(query, VECTORSTORES)
    context = merge_results(search_results)
    response = generate_response(query, context, model_name)
    return {"query": query, "response": response, "context": context}

# FastAPI 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
