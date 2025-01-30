from fastapi import APIRouter

router = APIRouter()

@router.get("/projectslist")
async def get_projects():
    """GitHub 프로젝트 목록 반환"""
    return [
        {"name": "reacto"},
        {"name": "trails"},
        {"name": "spring-framework-4-reference"},
        {"name": "welcome-android"},
        {"name": "react-instantsearch"},
        {"name": "WZLBadge"},
    ]
