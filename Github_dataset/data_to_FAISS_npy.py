import os
import pandas as pd
import numpy as np
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore  # 올바른 import 경로

# HuggingFace Embeddings 설정
EMBEDDINGS = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")


def process_csv(file_path, data_type, project_name):
    df = pd.read_csv(file_path)
    documents = []
    
    if data_type == "commits":
        for _, row in df.iterrows():
            content = f"Commit Message: {row['Message']} (Author: {row['Author']}, Date: {row['Date']})"
            metadata = {"type": "commit", "author": row["Author"], "date": row["Date"], "project": project_name}
            documents.append(Document(page_content=content, metadata=metadata))
    
    elif data_type == "pull_requests":
        for _, row in df.iterrows():
            content = (
                f"PR Title: {row['Title']} (Author: {row['Author']}, State: {row['State']}, "
                f"Created At: {row['Created At']}, Merged At: {row.get('Merged At', 'N/A')}, "
                f"Closed At: {row.get('Closed At', 'N/A')})"
            )
            metadata = {
                "type": "pull_request",
                "author": row["Author"],
                "state": row["State"],
                "created_at": row["Created At"],
                "merged_at": row.get("Merged At", None),
                "closed_at": row.get("Closed At", None),
                "project": project_name
            }
            documents.append(Document(page_content=content, metadata=metadata))
    
    elif data_type == "issues":
        for _, row in df.iterrows():
            content = (
                f"Issue Title: {row['Title']} (State: {row['State']}, Created At: {row['Created At']}, "
                f"Closed At: {row.get('Closed At', 'N/A')})"
            )
            metadata = {
                "type": "issue",
                "state": row["State"],
                "created_at": row["Created At"],
                "closed_at": row.get("Closed At", None),
                "project": project_name
            }
            documents.append(Document(page_content=content, metadata=metadata))
    
    elif data_type == "contributors":
        for _, row in df.iterrows():
            content = f"Contributor: {row['Name']} (Commits: {row['Commit Count']})"
            metadata = {"type": "contributor", "name": row["Name"], "commits": row["Commit Count"], "project": project_name}
            documents.append(Document(page_content=content, metadata=metadata))
    
    return documents


def create_vectorstore_for_project(project_path, project_name, output_dir):
    data_types = ["commits", "pull_requests", "contributors", "issues"]
    all_documents = []

    for data_type in data_types:
        file_path = os.path.join(project_path, f"{project_name}_{data_type}.csv")
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        documents = process_csv(file_path, data_type, project_name)
        if not documents:
            print(f"No {data_type} data found for project: {project_name}")
            continue

        all_documents.extend(documents)
    
    if not all_documents:
        print(f"No documents to process for project: {project_name}")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunked_documents = text_splitter.split_documents(all_documents)

    # 긴 텍스트 필터링
    chunked_documents = [doc for doc in chunked_documents if len(doc.page_content) <= 1000]
    if not chunked_documents:
        print(f"No chunked documents for project: {project_name}")
        return

    # 임베딩 계산
    doc_texts = [doc.page_content for doc in chunked_documents]
    vectors = EMBEDDINGS.embed_documents(doc_texts)
    vectors_np = np.array(vectors, dtype=np.float32)

    # 임베딩 저장
    os.makedirs(output_dir, exist_ok=True)
    embeddings_file_path = os.path.join(output_dir, f"{project_name}_embeddings.npy")
    np.save(embeddings_file_path, vectors_np)
    print(f"Embeddings for {project_name} saved to {embeddings_file_path}")

    # 메타데이터 리스트
    metadatas = [doc.metadata for doc in chunked_documents]

    # (text, embedding) 형태의 리스트 생성
    text_embeddings = [(text, vec.tolist()) for text, vec in zip(doc_texts, vectors_np)]

    # 클러스터 수 동적 설정
    num_vectors = len(vectors_np)
    min_training_per_cluster = 10  # 각 클러스터당 최소 벡터 수
    nlist = max(1, min(30, num_vectors // min_training_per_cluster))  # 동적 클러스터 수 설정

    print(f"Creating FAISS IVF index with nlist={nlist} for project: {project_name}")

    # IVF 인덱스 생성
    D = vectors_np.shape[1]
    quantizer = faiss.IndexFlatL2(D)
    ivf_index = faiss.IndexIVFFlat(quantizer, D, nlist, faiss.METRIC_L2)
    
    # IVF 인덱스 훈련
    ivf_index.train(vectors_np)
    ivf_index.add(vectors_np)

    # docstore 생성
    docstore_records = {str(i): doc for i, doc in enumerate(chunked_documents)}
    docstore = InMemoryDocstore(docstore_records)
    index_to_docstore_id = {i: str(i) for i in range(len(chunked_documents))}

    # VectorStore 생성 (Flat 대신 IVF 인덱스를 사용)
    vectorstore = FAISS(
        embedding_function=EMBEDDINGS,  # Embeddings 객체로 설정
        index=ivf_index,
        docstore=docstore,
        index_to_docstore_id=index_to_docstore_id
    )

    vectorstore.save_local(os.path.join(output_dir, f"{project_name}"))
    print(f"IVF Vectorstore for {project_name} saved in {output_dir}")


def process_all_projects(base_dir, output_dir):
    projects_file = os.path.join(base_dir, "all_projects.csv")
    if not os.path.exists(projects_file):
        print(f"File not found: {projects_file}")
        return

    projects_df = pd.read_csv(projects_file)
    if "Name" not in projects_df.columns:
        print(f"'Name' column missing in {projects_file}")
        return

    for _, row in projects_df.iterrows():
        project_name = row["Name"]
        project_path = os.path.join(base_dir, project_name)
        
        if not os.path.isdir(project_path):
            print(f"Project directory not found: {project_path}")
            continue

        create_vectorstore_for_project(project_path, project_name, output_dir)


# 실행
BASE_DIR = "./data"
OUTPUT_DIR = "./vectorstores_npy_cluster22"

process_all_projects(base_dir=BASE_DIR, output_dir=OUTPUT_DIR)
