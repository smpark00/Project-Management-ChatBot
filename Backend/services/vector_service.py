import os
import json
import numpy as np
import pandas as pd
import faiss
from pathlib import Path
from langchain.schema import Document
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

BASE_DIRECTORY = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage")))
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)

def build_vector_database(repo_name: str):
    """CSV 데이터를 기반으로 벡터 데이터베이스 구축"""
    project_path = BASE_DIRECTORY / repo_name / "csv"
    print(f"Building vector database for {repo_name}...")
    if not project_path.exists():
        raise ValueError(f"CSV directory not found for {repo_name}")

    issues_path = project_path / f"{repo_name}_issues.csv"
    prs_path = project_path / f"{repo_name}_pull_requests.csv"
    commits_path = project_path / f"{repo_name}_commits.csv"

    if not issues_path.exists() or not prs_path.exists() or not commits_path.exists():
        raise ValueError("One or more CSV files are missing")

    issues_df = pd.read_csv(issues_path)
    prs_df = pd.read_csv(prs_path)
    commits_df = pd.read_csv(commits_path)

    all_texts, metadata, doc_ids = [], [], []

    for _, row in issues_df.iterrows():
        text = f"Issue: {row['Title']}, State: {row['State']}"
        all_texts.append(text)
        metadata.append({"type": "issue", "original_data": row.to_dict()})
        doc_ids.append(str(row["ID"]))

    for _, row in prs_df.iterrows():
        text = f"PR: {row['Title']}, State: {row['State']}"
        all_texts.append(text)
        metadata.append({"type": "pull_request", "original_data": row.to_dict()})
        doc_ids.append(str(row["ID"]))

    for _, row in commits_df.iterrows():
        text = f"Commit: {row['Message']}, Author: {row['Author']}"
        all_texts.append(text)
        metadata.append({"type": "commit", "original_data": row.to_dict()})
        doc_ids.append(str(row["ID"]))

    docs = [Document(page_content=text) for text in all_texts]

    embedding_vectors = embeddings.embed_documents(all_texts)
    embedding_vectors = np.array(embedding_vectors, dtype="float32")

    d = embedding_vectors.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(embedding_vectors)

    doc_dict = {doc_ids[i]: docs[i] for i in range(len(docs))}
    docstore = InMemoryDocstore(doc_dict)
    index_to_docstore_id = {str(i): doc_ids[i] for i in range(len(docs))}

    vectorstore = FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=docstore,
        index_to_docstore_id=index_to_docstore_id,
    )

    vectorstore_dir = BASE_DIRECTORY / repo_name / "vectorstore"
    vectorstore_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(vectorstore_dir))

    with open(vectorstore_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return {
        "message": "Vector database built successfully.",
        "csv_directory": str(project_path),
        "vectorstore_directory": str(vectorstore_dir),
        "metadata_file": str(vectorstore_dir / "metadata.json")
    }
