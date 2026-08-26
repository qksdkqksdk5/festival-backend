import os
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CrawlTask, TaskStatus
from app.schemas import CrawlRequest, TaskStatusResponse
from app.tasks.crawl_tasks import crawl_festivals_task, run_crawl_process

# USE_CELERY 환경변수가 True이면 Celery, False이면 BackgroundTasks 사용
USE_CELERY = os.getenv("USE_CELERY", "False").lower() in ("true", "1", "t")

router = APIRouter(tags=["Crawl"])


@router.post("/crawl", response_model=dict)
def request_crawl(
    payload: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    축제 크롤링 작업을 요청합니다. (USE_CELERY 환경변수에 따라 Celery 또는 BackgroundTasks로 실행)
    """
    task_id = str(uuid.uuid4())

    db_task = CrawlTask(
        task_id=task_id,
        keyword=payload.keyword,
        status=TaskStatus.PENDING
    )
    db.add(db_task)
    db.commit()

    if USE_CELERY:
        crawl_festivals_task.delay(task_id, payload.keyword)
        message = f"'{payload.keyword}' 키워드 축제 크롤링 작업이 Celery로 등록되었습니다."
    else:
        background_tasks.add_task(run_crawl_process, task_id=task_id, keyword=payload.keyword)
        message = f"'{payload.keyword}' 키워드 축제 크롤링 작업이 등록되었습니다."

    return {
        "task_id": task_id,
        "status": TaskStatus.PENDING,
        "message": message
    }


@router.get("/crawl/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """
    작업 진행 상태를 조회합니다.
    """
    task = db.query(CrawlTask).filter_by(task_id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="해당 작업(task_id)을 찾을 수 없습니다.")
    return task