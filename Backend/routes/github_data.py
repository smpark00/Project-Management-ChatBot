import os
import requests
import zipfile
from fastapi import FastAPI, HTTPException, Body
from pathlib import Path
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

router = APIRouter()

# .env 파일 로드
load_dotenv("../../.env")

# 저장 경로 설정
BASE_DIRECTORY = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage")))

# GitHub Personal Access Token (환경 변수에서 가져오기)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

@router.post("/download")
async def download_repository(repo_url: str):
    """
    GitHub 저장소를 다운로드하고 로컬에 저장
    """
    try:
        # 1. URL 검증
        if not repo_url.startswith("https://github.com/"):
            raise HTTPException(status_code=400, detail="Invalid GitHub URL")

        # 2. 저장소 정보 추출
        repo_parts = repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid GitHub repository format")
        owner, repo = repo_parts[0], repo_parts[1]
        repo = repo.replace(".git", "")  # .git 제거

        # 3. GitHub API 요청 URL 생성
        api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"

        # 4. 헤더에 인증 추가
        headers = {}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"

        # 5. ZIP 파일 다운로드
        response = requests.get(api_url, headers=headers, stream=True)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to download repository: {response.json().get('message', '')}")

        # 6. ZIP 파일 저장
        zip_path = BASE_DIRECTORY / f"{repo}.zip"  # 경로 수정
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)

        # 7. ZIP 파일 압축 해제
        extract_path = BASE_DIRECTORY / repo  # 경로 수정
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        # 8. 결과 반환
        return {
            "message": "Repository downloaded and extracted successfully.",
            "repository_name": repo,
            "files": [str(p.relative_to(BASE_DIRECTORY)) for p in extract_path.rglob("*") if p.is_file()],
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {repr(e)}")