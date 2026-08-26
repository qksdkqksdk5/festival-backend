import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CrawlTask, TaskStatus
from app.schemas import CrawlRequest, TaskStatusResponse
from app.tasks.crawl_tasks import crawl_festivals_task

# prefix는 main.py에서 일괄 관리하도록 제외하고 tags만 지정합니다.
router = APIRouter(tags=["Crawl"])


@router.post("/crawl", response_model=dict)
def request_crawl(payload: CrawlRequest, db: Session = Depends(get_db)):
    """
    축제 크롤링 작업을 백그라운드 Celery Worker에 요청합니다.
    """
    task_id = str(uuid.uuid4())

    db_task = CrawlTask(
        task_id=task_id,
        keyword=payload.keyword,
        status=TaskStatus.PENDING
    )
    db.add(db_task)
    db.commit()

    crawl_festivals_task.delay(task_id, payload.keyword)

    return {
        "task_id": task_id,
        "status": TaskStatus.PENDING,
        "message": f"'{payload.keyword}' 키워드 축제 크롤링 작업이 등록되었습니다."
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