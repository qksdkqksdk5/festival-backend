from app.worker import celery_app
from app.database import SessionLocal
from app.models import CrawlTask, Festival, TaskStatus
from app.services.crawler import run_festival_crawler


@celery_app.task(bind=True, max_retries=2)
def crawl_festivals_task(self, task_id: str, keyword: str = "서울", max_pages: int = 10):
    db = SessionLocal()
    try:
        task = db.query(CrawlTask).filter_by(task_id=task_id).first()
        if task:
            task.status = TaskStatus.IN_PROGRESS
            db.commit()

        festivals_data = run_festival_crawler(keyword=keyword, max_pages=max_pages)

        saved_count = 0
        for data in festivals_data:
            # title과 period가 동일한 축제가 이미 DB에 있는지 확인
            existing_festival = (
                db.query(Festival)
                .filter(Festival.title == data["title"], Festival.period == data["period"])
                .first()
            )

            if existing_festival:
                # 이미 존재하면 최신 정보로 업데이트 (Upsert - Update)
                existing_festival.location = data["location"]
                existing_festival.image_url = data["image_url"]
                existing_festival.detail_url = data["detail_url"]
                existing_festival.task_id = task_id
            else:
                # 없으면 신규 저장 (Upsert - Insert)
                festival = Festival(
                    id=data["id"],
                    task_id=task_id,
                    title=data["title"],
                    period=data["period"],
                    location=data["location"],
                    image_url=data["image_url"],
                    detail_url=data["detail_url"],
                )
                db.add(festival)
                saved_count += 1

        if task:
            task.status = TaskStatus.COMPLETED
            task.total_count = str(len(festivals_data))
            db.commit()

        return {"status": "SUCCESS", "total_crawled": len(festivals_data), "new_saved": saved_count}

    except Exception as exc:
        db.rollback()
        task = db.query(CrawlTask).filter_by(task_id=task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            db.commit()
        raise self.retry(exc=exc, countdown=5)
    finally:
        db.close()