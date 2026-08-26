from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_  # 💡 1. or_ 추가
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Festival

router = APIRouter(tags=["Festivals"])


@router.get("/festivals")
def get_festivals(
    keyword: Optional[str] = Query(None, description="제목 또는 상세장소 검색어"),
    region: Optional[str] = Query(None, description="시/도 지역 필터 (예: 서울, 대구)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Festival)

    # 1. 지역 필터링: '대구'와 일치하거나 '대구 '(공백)으로 시작하는 경우만 매칭
    if region and region != "전체":
        query = query.filter(
            or_(
                Festival.location == region,
                Festival.location.ilike(f"{region} %")
            )
        )

    # 2. 일반 검색어 필터링: 빈 문자열이 아닐 때만 수행
    if keyword and keyword.strip():
        search_val = keyword.strip()
        query = query.filter(
            (Festival.title.ilike(f"%{search_val}%")) | (Festival.location.ilike(f"%{search_val}%"))
        )

    total = query.count()
    festivals = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": festivals,
    }