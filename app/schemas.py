from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models import TaskStatus

# 크롤링 요청 데이터
class CrawlRequest(BaseModel):
    keyword: Optional[str] = "전국"  # 기본값: 전국 축제

# 축제 정보 응답
class FestivalResponse(BaseModel):
    id: str
    title: str
    period: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    detail_url: Optional[str] = None

    class Config:
        from_attributes = True

# 작업 상태 및 수집 결과 응답
class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    keyword: Optional[str] = None
    created_at: datetime
    festivals: List[FestivalResponse] = []

    class Config:
        from_attributes = True