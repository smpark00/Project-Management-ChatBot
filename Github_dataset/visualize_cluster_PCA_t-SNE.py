import os
import numpy as np
import faiss
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE


def load_faiss_and_labels(project_dir, data_type):
    """
    특정 프로젝트 및 데이터 유형의 FAISS와 관련 데이터를 로드합니다.

    Args:
        project_dir (str): 프로젝트 디렉토리 경로.
        data_type (str): 데이터 유형 (commits, issues, pull_requests).

    Returns:
        np.ndarray: 벡터 데이터.
        np.ndarray: 라벨 데이터.
        faiss.Index: FAISS 인덱스.
    """
    data_type_dir = os.path.join(project_dir, data_type)
    index_path = os.path.join(data_type_dir, "index.faiss")
    embeddings_path = os.path.join(data_type_dir, "embeddings.npy")
    labels_path = os.path.join(data_type_dir, "labels.npy")

    if not os.path.exists(index_path) or not os.path.exists(embeddings_path) or not os.path.exists(labels_path):
        print(f"Data missing for {data_type} in {project_dir}")
        return None, None, None

    # 로드
    index = faiss.read_index(index_path)
    embeddings = np.load(embeddings_path).astype("float32")
    labels = np.load(labels_path)

    return embeddings, labels, index


def visualize_clusters(base_dir, output_dir, use_tsne=True, perplexity=30, random_state=42):
    """
    모든 프로젝트의 클러스터링 결과를 시각화합니다.

    Args:
        base_dir (str): 벡터 데이터 저장 디렉토리.
        output_dir (str): 출력 디렉토리 경로.
        use_tsne (bool): t-SNE를 사용할지 여부 (True면 t-SNE, False면 PCA 사용).
        perplexity (int): t-SNE perplexity 값.
        random_state (int): t-SNE 및 PCA의 랜덤 시드.
    """
    projects = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    all_embeddings = []
    all_labels = []

    for project in projects:
        project_dir = os.path.join(base_dir, project)
        data_types = ["commits", "issues", "pull_requests"]

        for data_type in data_types:
            embeddings, labels, index = load_faiss_and_labels(project_dir, data_type)
            if embeddings is None or labels is None or index is None:
                continue

            # 클러스터 ID 추출
            print(f"Processing {project}_{data_type}")
            _, cluster_assignments = index.search(embeddings, 1)
            cluster_assignments = cluster_assignments.flatten()

            # 각 데이터 포인트의 라벨에 클러스터 ID 추가
            labels_with_cluster = [f"{label}_cluster_{cluster_id}" for label, cluster_id in zip(labels, cluster_assignments)]

            # 전체 데이터 통합
            all_embeddings.append(embeddings)
            all_labels.extend(labels_with_cluster)

    # 데이터 통합
    if len(all_embeddings) == 0:
        print("No data available for visualization.")
        return

    all_embeddings = np.vstack(all_embeddings)

    # 차원 축소
    if use_tsne:
        print("Applying t-SNE for dimensionality reduction...")
        tsne = TSNE(n_components=2, perplexity=perplexity, random_state=random_state)
        reduced_embeddings = tsne.fit_transform(all_embeddings)
    else:
        print("Applying PCA for dimensionality reduction...")
        pca = PCA(n_components=2, random_state=random_state)
        reduced_embeddings = pca.fit_transform(all_embeddings)

    # 시각화
    print("Visualizing clusters...")
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(
        reduced_embeddings[:, 0],
        reduced_embeddings[:, 1],
        c=[hash(label) % 20 for label in all_labels],  # 색상은 해시 기반
        cmap="tab20",
        s=10
    )
    plt.colorbar(scatter, label="Cluster ID")
    plt.title("FAISS Clustering Visualization")
    plt.xlabel("Component 1")
    plt.ylabel("Component 2")
    plt.grid(True)
    plt.show()


# 실행
BASE_DIR = "./vectorstores_with_labels_each_project"
OUTPUT_DIR = "./visualizations"

visualize_clusters(base_dir=BASE_DIR, output_dir=OUTPUT_DIR, use_tsne=True)
