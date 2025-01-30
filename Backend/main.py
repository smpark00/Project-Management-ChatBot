from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import chat, project_load

app = FastAPI()

# CORS 설정
origins = [
    "http://localhost:3000",  # React 개발 서버
    "http://localhost:5173",  # Vite 개발 서버
    "https://your-production-domain.com",  # 배포된 프론트엔드 도메인
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 출처
    allow_credentials=True,  # 인증 정보 포함 여부
    allow_methods=["*"],  # 허용할 HTTP 메서드 (GET, POST, PUT 등)
    allow_headers=["*"],  # 허용할 HTTP 헤더
)

app.include_router(chat.router)
app.include_router(project_load.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
