from fastapi import APIRouter, HTTPException, Query
from services.github_service import download_github_repo

router = APIRouter()

@router.post("/download")
async def download_repository(repo_url: str = Query(...)):
    """
    GitHub 저장소를 다운로드하고 로컬에 저장한 후, 데이터를 CSV로 저장
    """
    try:
        repo_name = download_github_repo(repo_url)
        return {"message": "Repository data successfully saved.", "repository_name": repo_name}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {repr(e)}")
