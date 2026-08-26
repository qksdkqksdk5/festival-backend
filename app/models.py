import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class CrawlTask(Base):
    __tablename__ = "crawl_tasks"

    task_id = Column(String, primary_key=True, index=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    keyword = Column(String, nullable=True)          # 검색한 키워드 또는 지역
    total_count = Column(String, nullable=True)      # 크롤링된 건수
    created_at = Column(DateTime, default=datetime.utcnow)

    # 1:N 관계 (하나의 작업으로 여러 축제 수집)
    festivals = relationship("Festival", back_populates="task", cascade="all, delete-orphan")

class Festival(Base):
    __tablename__ = "festivals"

    id = Column(String, primary_key=True, index=True)  # 데이터 식별 id
    task_id = Column(String, ForeignKey("crawl_tasks.task_id"), nullable=False)
    title = Column(String, nullable=False)           # 축제 이름
    period = Column(String, nullable=True)           # 축제 기간
    location = Column(String, nullable=True)         # 장소/지역
    image_url = Column(Text, nullable=True)          # 대표 이미지 URL
    detail_url = Column(Text, nullable=True)         # 상세페이지 URL
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("CrawlTask", back_populates="festivals")