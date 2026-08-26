from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 추가
from app.api.v1.crawl import router as crawl_router
from app.api.v1.festivals import router as festivals_router
from app.database import engine, Base
from app.core.config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

# ----------------- CORS 설정 추가 -----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite React 기본 포트 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------------------------------------

app.include_router(crawl_router, prefix="/api/v1")
app.include_router(festivals_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": f"{settings.PROJECT_NAME}가 정상 작동 중입니다."}