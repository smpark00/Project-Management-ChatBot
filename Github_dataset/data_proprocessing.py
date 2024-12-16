import os
import pandas as pd
import json
import numpy as np
import faiss
from langchain.schema import Document
from langchain.docstore.in_memory import InMemoryDocstore
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

root_dir = './data'
all_projects_path = os.path.join(root_dir, "all_projects.csv")
projects_df = pd.read_csv(all_projects_path)

def issue_to_text(row, project_name):
    return f"Project: {project_name}, Issue ID: {row['ID']}, Project ID: {row['Project ID']}, Title: {row['Title']}, State: {row['State']}, Created At: {row['Created At']}, Closed At: {row.get('Closed At', 'N/A')}"

def pr_to_text(row, project_name):
    return f"Project: {project_name}, Pull Request ID: {row['ID']}, Project ID: {row['Project ID']}, Title: {row['Title']}, Author: {row['Author']}, State: {row['State']}, Created At: {row['Created At']}, Merged At: {row.get('Merged At', 'N/A')}, Closed At: {row.get('Closed At', 'N/A')}"

def commit_to_text(row, project_name):
    return f"Project: {project_name}, Commit ID: {row['ID']}, Project ID: {row['Project ID']}, Author: {row['Author']}, Date: {row['Date']}, Message: {row['Message']}"

all_texts = []
metadata = []

for _, proj_row in projects_df.iterrows():
    project_name = proj_row['Name']
    project_dir = os.path.join(root_dir, project_name)

    issues_path = os.path.join(project_dir, f"{project_name}_issues.csv")
    prs_path = os.path.join(project_dir, f"{project_name}_pull_requests.csv")
    commits_path = os.path.join(project_dir, f"{project_name}_commits.csv")

    if not os.path.isfile(issues_path):
        print(f"Warning: {issues_path} not found.")
        continue
    if not os.path.isfile(prs_path):
        print(f"Warning: {prs_path} not found.")
        continue
    if not os.path.isfile(commits_path):
        print(f"Warning: {commits_path} not found.")
        continue

    issues_df = pd.read_csv(issues_path)
    prs_df = pd.read_csv(prs_path)
    commits_df = pd.read_csv(commits_path)

    for _, r in issues_df.iterrows():
        text = issue_to_text(r, project_name)
        all_texts.append(text)
        metadata.append({"project_name": project_name, "type": "issue", "original_data": r.to_dict()})

    for _, r in prs_df.iterrows():
        text = pr_to_text(r, project_name)
        all_texts.append(text)
        metadata.append({"project_name": project_name, "type": "pull_request", "original_data": r.to_dict()})

    for _, r in commits_df.iterrows():
        text = commit_to_text(r, project_name)
        all_texts.append(text)
        metadata.append({"project_name": project_name, "type": "commit", "original_data": r.to_dict()})

model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=model_name)

docs = [Document(page_content=text) for text in all_texts]

doc_dict = {str(i): docs[i] for i in range(len(docs))}
docstore = InMemoryDocstore(doc_dict)

# 임베딩 벡터 생성
embedding_vectors = embeddings.embed_documents(all_texts)
embedding_vectors = np.array(embedding_vectors, dtype='float32')

d = embedding_vectors.shape[1]
print(f"Embedding dimension (d): {d}")

index = faiss.IndexFlatL2(d)
index.add(embedding_vectors)
print(f"FAISS index size: {index.ntotal}")

# embedding_function에 Embeddings 객체를 직접 전달
vectorstore = FAISS(
    embedding_function=embeddings,
    index=index,
    docstore=docstore,
    index_to_docstore_id={str(i): str(i) for i in range(len(docs))}
)

vectorstore_dir = "vectorstore_dir"
os.makedirs(vectorstore_dir, exist_ok=True)

# VectorStore 로컬 저장 (index.faiss, index.pkl 포함)
vectorstore.save_local(vectorstore_dir)
print("VectorStore saved to vectorstore_dir")

# all_texts_backup.txt 저장
with open(os.path.join(vectorstore_dir, "all_texts_backup.txt"), "w", encoding="utf-8") as f:
    for line in all_texts:
        f.write(line + "\n")

# metadata.json 저장
with open(os.path.join(vectorstore_dir, "metadata.json"), "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

# docstore.json 저장
# Document 객체는 직렬화 불가하므로 page_content만 추출
serializable_doc_dict = {k: {"page_content": v.page_content} for k, v in doc_dict.items()}
with open(os.path.join(vectorstore_dir, "docstore.json"), "w", encoding="utf-8") as f:
    json.dump(serializable_doc_dict, f, ensure_ascii=False, indent=2)

print("Files saved to vectorstore_dir:")
print(" - index.faiss")
print(" - all_texts_backup.txt")
print(" - metadata.json")
print(" - docstore.json")

# 문서 확인: InMemoryDocstore는 search(key) 메서드를 통해 문서 접근
for i in range(min(5, len(docs))):
    doc = docstore.search(str(i))
    print(f"Document {i}: {doc}")
