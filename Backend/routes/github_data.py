from fastapi import APIRouter, HTTPException, Query
from services.github_service import download_github_repo
from services.vector_service import build_vector_database

router = APIRouter()

@router.post("/download")
async def download_repository(repo_url: str = Query(...)):
    """
    GitHub 저장소를 다운로드하고 로컬에 저장한 후, 데이터를 CSV로 저장
    """
    try:
        repo_name = download_github_repo(repo_url)
    
        vector_db_result = build_vector_database(repo_name)

        return {
            "message": "Repository data successfully saved and vector database built.",
            "repository_name": repo_name,
            "csv_directory": vector_db_result["csv_directory"],
            "vectorstore_directory": vector_db_result["vectorstore_directory"],
            "metadata_file": vector_db_result["metadata_file"]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {repr(e)}")
