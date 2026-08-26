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

# CORS 설정 추가
origins = [
    "*"  # 테스트용: 모든 도메인 허용 (배포 시에는 프론트엔드 주소로 변경 추천)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"],  # 모든 헤더 허용
)

app.include_router(crawl_router, prefix="/api/v1")
app.include_router(festivals_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": f"{settings.PROJECT_NAME}가 정상 작동 중입니다."}