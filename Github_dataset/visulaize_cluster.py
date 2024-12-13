import os
import numpy as np
import faiss
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from langchain.schema import Document
from langchain.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def visualize_faiss_clusters_all_projects(output_dir, n_components=2, perplexity_default=30, random_state=42):
    """
    모든 프로젝트의 FAISS IVF 인덱스 클러스터링을 시각화합니다.
    
    Args:
        output_dir (str): 클러스터링된 벡터스토어가 저장된 디렉토리 경로
        n_components (int): 차원 축소 차원 (보통 2)
        perplexity_default (float): 기본 TSNE의 perplexity 값
        random_state (int): TSNE의 랜덤 상태
    """
    # HuggingFace Embeddings 설정 (이미 임베딩이 완료된 상태이므로 실제로는 필요 없음)
    EMBEDDINGS = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")
    
    # 프로젝트 리스트 가져오기
    projects = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
    
    for project in projects:
        project_dir = os.path.join(output_dir, project)
        index_path = os.path.join(project_dir, "index.faiss")
        embeddings_path = os.path.join(project_dir, "embeddings.npy")
        
        # 파일 존재 여부 확인
        if not os.path.exists(index_path):
            print(f"FAISS 인덱스 파일을 찾을 수 없습니다: {index_path}")
            continue
        if not os.path.exists(embeddings_path):
            print(f"임베딩 파일을 찾을 수 없습니다: {embeddings_path}")
            continue
        
        # FAISS 인덱스 로드
        try:
            index = faiss.read_index(index_path)
        except Exception as e:
            print(f"프로젝트 {project}의 FAISS 인덱스 로드 중 오류 발생: {e}")
            continue
        
        # 임베딩 로드
        try:
            embeddings = np.load(embeddings_path).astype('float32')  # FAISS는 float32 타입을 사용
        except Exception as e:
            print(f"프로젝트 {project}의 임베딩 로드 중 오류 발생: {e}")
            continue
        
        n_samples = embeddings.shape[0]
        if n_samples == 0:
            print(f"프로젝트 {project}에는 임베딩된 데이터가 없습니다.")
            continue
        
        # 클러스터 할당
        print(f"프로젝트 {project}의 클러스터 할당 중...")
        if not isinstance(index, faiss.IndexIVF):
            print(f"프로젝트 {project}의 인덱스는 IVF 인덱스가 아닙니다. 건너뜁니다.")
            continue
        
        # nprobe는 nlist보다 작거나 같아야 함
        nlist = index.nlist
        nprobe = min(10, nlist)  # 기본적으로 10, 클러스터 수가 작으면 그에 맞게 조정
        
        index.nprobe = nprobe
        distances, cluster_assignments = index.search(embeddings, 1)  # 가장 가까운 1개의 클러스터 찾기
        cluster_assignments = cluster_assignments.flatten()
        
        # t-SNE perplexity 조정
        perplexity = min(perplexity_default, max(5, n_samples - 1))
        
        if perplexity < 5:
            print(f"프로젝트 {project}의 데이터 포인트 수가 너무 적어 t-SNE perplexity를 5로 설정합니다.")
            perplexity = 5
        
        # 차원 축소
        print(f"프로젝트 {project}의 차원 축소 중 (perplexity={perplexity})...")
        try:
            tsne = TSNE(n_components=n_components, perplexity=perplexity, random_state=random_state)
            embeddings_2d = tsne.fit_transform(embeddings)
        except Exception as e:
            print(f"프로젝트 {project}의 t-SNE 실행 중 오류 발생: {e}")
            continue
        
        # 시각화
        print(f"프로젝트 {project}의 클러스터 시각화 중...")
        plt.figure(figsize=(10, 8))
        scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], c=cluster_assignments, cmap='tab20', s=10)
        plt.colorbar(scatter, label='Cluster ID')
        plt.title(f"Project: {project}'s FAISS IVF Clustering visulaization")
        plt.xlabel("TSNE Componenet 1")
        plt.ylabel("TSNE Component 2")
        plt.grid(True)
        plt.show()

# 사용 예시
if __name__ == "__main__":
    # 시각화하고자 하는 프로젝트들의 벡터스토어 디렉토리 상위 경로
    # 예: "./vectorstores_npy_cluster/"
    vectorstores_directory = "./vectorstores_npy_cluster"  # 실제 벡터스토어 디렉토리 경로로 변경
    
    visualize_faiss_clusters_all_projects(
        output_dir=vectorstores_directory,
        n_components=2,
        perplexity_default=30,
        random_state=42
    )
