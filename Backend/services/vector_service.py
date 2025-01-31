import os
import json
import pandas as pd
from pathlib import Path
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

BASE_DIRECTORY = Path(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage"))
)
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class VectorStoreService:
    def __init__(
        self,
        base_directory: Path = BASE_DIRECTORY,
        embeddings_model_name: str = MODEL_NAME,
    ):
        self.base_directory = Path(base_directory).resolve()
        self.embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

    def get_vectorstore_path(self, repo_name: str) -> Path:
        """프로젝트별 벡터스토어가 저장될 경로를 반환"""
        return self.base_directory / repo_name / "vectorstore"

    def build_vector_database(self, repo_name: str) -> dict:
        """
        CSV 데이터에서 필요한 텍스트를 추출하여 FAISS 벡터스토어를 생성 및 저장
        """
        csv_dir = self.base_directory / repo_name / "csv"
        if not csv_dir.exists():
            raise FileNotFoundError(f"CSV 폴더가 존재하지 않습니다: {csv_dir}")

        csv_files = [
            f"{repo_name}_commits.csv",
            f"{repo_name}_issues.csv",
            f"{repo_name}_pull_requests.csv",
        ]

        df_list = []
        for filename in csv_files:
            path = csv_dir / filename
            if path.exists():
                temp_df = pd.read_csv(path)
                df_list.append(temp_df)
            else:
                print(f"⚠️ CSV 파일이 없어 스킵합니다: {path}")

        if not df_list:
            raise FileNotFoundError(
                f"'{repo_name}' 관련 CSV가 하나도 존재하지 않습니다. ({csv_dir})"
            )

        df = pd.concat(df_list, ignore_index=True)
        print(f"✅ CSV {len(df_list)}개를 합쳐서 총 {len(df)}개 레코드를 얻었습니다.")

        docs = []
        doc_dict = {}  # ✅ docstore.json 저장용
        index_to_docstore_id = {}  # ✅ index_to_docstore_id.json 저장용

        for idx, row in df.iterrows():
            if "ID" not in row:
                raise ValueError(
                    "CSV에 'ID' 컬럼이 없습니다. doc_id를 뭘로 쓸지 결정해야 합니다."
                )

            doc_id = str(row["ID"]).strip()

            # 🔹 Title, Message, Body 등의 필드를 합쳐 문서 내용 생성
            content_parts = []
            if "Title" in row and pd.notna(row["Title"]):
                content_parts.append(f"Title: {row['Title']}")
            if "Message" in row and pd.notna(row["Message"]):
                content_parts.append(f"Message: {row['Message']}")
            if "Body" in row and pd.notna(row["Body"]):
                content_parts.append(f"Body: {row['Body']}")
            content = (
                "\n".join(content_parts) if content_parts else "No content available."
            )

            filename = row.get("filename", f"file_{doc_id}")

            doc = Document(
                page_content=content, metadata={"source": filename, "id": doc_id}
            )
            docs.append(doc)

            # ✅ JSON 직렬화 가능하도록 저장
            doc_dict[doc_id] = {"page_content": content}

            # ✅ FAISS 인덱스와 매핑을 맞추기 위해 idx를 사용
            index_to_docstore_id[str(idx)] = doc_id

        print(f"✅ Document 객체 생성 완료. 총 {len(docs)}개")

        # 3) FAISS 벡터스토어 생성 & 저장
        vectorstore = FAISS.from_documents(docs, self.embeddings)
        vectorstore.index_to_docstore_id = (
            index_to_docstore_id  # ✅ FAISS 객체에 직접 매핑 추가
        )

        vectorstore_path = self.get_vectorstore_path(repo_name)
        vectorstore_path.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(str(vectorstore_path))

        # ✅ index_to_docstore_id.json 저장
        index_mapping_path = vectorstore_path / "index_to_docstore_id.json"
        with open(index_mapping_path, "w", encoding="utf-8") as f:
            json.dump(index_to_docstore_id, f, ensure_ascii=False, indent=2)

        # ✅ docstore.json 저장
        docstore_path = vectorstore_path / "docstore.json"
        with open(docstore_path, "w", encoding="utf-8") as f:
            json.dump(doc_dict, f, ensure_ascii=False, indent=2)

        print(f"✅ 벡터스토어가 성공적으로 생성 및 저장되었습니다: {vectorstore_path}")

        return {
            "vectorstore_directory": str(vectorstore_path),
            "docstore_file": str(docstore_path),
            "index_to_docstore_file": str(index_mapping_path),
            "doc_count": len(docs),
        }
