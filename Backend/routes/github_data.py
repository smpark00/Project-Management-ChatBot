from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from services.github_service import download_github_repo
from services.vector_service import build_vector_database
import asyncio
import json

router = APIRouter()

async def progress_stream(repo_url: str):
    """
    GitHub 저장소 다운로드 및 벡터 데이터베이스 구축 진행률을 SSE 방식으로 스트리밍
    """
    try:
        total_steps = 100
        current_progress = 0

        async def update_progress(step_count, status_message):
            """ 진행률을 업데이트하면서 프론트엔드로 전송 """
            nonlocal current_progress
            for _ in range(step_count):
                current_progress += 1
                yield f"data: {json.dumps({'progress': current_progress, 'status': status_message})}\n\n"
                await asyncio.sleep(0.1)  # 🎯 비동기 대기

        # 1️⃣ GitHub 저장소 다운로드 (총 30%)
        yield f"data: {json.dumps({'progress': current_progress, 'status': 'Starting repository download'})}\n\n"
        repo_name = await asyncio.to_thread(download_github_repo, repo_url)
        async for progress in update_progress(30, "Downloading repository completed."):
            yield progress

        # 2️⃣ 벡터 데이터베이스 구축 (총 70%)
        yield f"data: {json.dumps({'progress': current_progress, 'status': 'Building vector database'})}\n\n"
        vector_db_result = await asyncio.to_thread(build_vector_database, repo_name)
        async for progress in update_progress(70, "Building vector database."):
            yield progress

        # 🎯 최종 완료
        yield f"""data: {json.dumps({
            'progress': 100,
            'status': 'Process complete',
            'repository_name': repo_name,
            'vectorstore_directory': vector_db_result['vectorstore_directory']
        })}\n\n"""

    except HTTPException as e:
        yield f"data: {json.dumps({'progress': 0, 'status': 'Error', 'message': str(e.detail)})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'progress': 0, 'status': 'Error', 'message': str(e)})}\n\n"

@router.get("/progress")
async def progress(repo_url: str = Query(...)):
    """
    진행률을 스트리밍 응답으로 반환 (프론트엔드에서 실시간으로 확인 가능)
    """
    return StreamingResponse(progress_stream(repo_url), media_type="text/event-stream")
