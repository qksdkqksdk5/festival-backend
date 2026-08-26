from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL이 .env 파일에 설정되지 않았습니다.")

# Supabase 연결 유지를 위한 pool_pre_ping 설정
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# DB 세션 생성기
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 모델 기본 클래스
Base = declarative_base()


# FastAPI Dependency용 DB 세션 제너레이터
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()