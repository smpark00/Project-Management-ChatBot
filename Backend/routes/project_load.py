import os
from fastapi import APIRouter, HTTPException

router = APIRouter()

# 기본 디렉토리 경로 설정 (필요에 따라 수정)
BASE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage"))

@router.get("/projectslist")
async def get_projects():
    """
    디렉토리 기반 GitHub 프로젝트 목록 반환
    """
    try:
        # 디렉토리가 존재하지 않으면 예외 발생
        if not os.path.exists(BASE_DIRECTORY):
            raise HTTPException(status_code=404, detail="Base directory not found")

        # 하위 디렉토리 이름들만 가져오기
        directories = [
            d for d in os.listdir(BASE_DIRECTORY)
            if os.path.isdir(os.path.join(BASE_DIRECTORY, d))
        ]

        # 디렉토리 이름 반환
        return [{"name": dir_name} for dir_name in directories]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
