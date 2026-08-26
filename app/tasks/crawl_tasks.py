import logging
from app.worker import celery_app
from app.database import SessionLocal
from app.models import CrawlTask, Festival, TaskStatus
from app.services.crawler import run_festival_crawler

# Uvicorn 및 서버 시스템 표준 로거 설정
logger = logging.getLogger("uvicorn.error")


def run_crawl_process(task_id: str, keyword: str = "서울", max_pages: int = 10):
    """
    실제 크롤링 및 DB 저장을 수행하는 공통 로직 (BackgroundTasks 및 Celery 공용)
    """
    logger.info(f"🚀 [CRAWL START] Task ID: {task_id} | Keyword: '{keyword}' | Max Pages: {max_pages}")
    
    db = SessionLocal()
    try:
        task = db.query(CrawlTask).filter_by(task_id=task_id).first()
        if task:
            task.status = TaskStatus.IN_PROGRESS
            db.commit()
            logger.info(f"🔄 Task {task_id} 상태 변경 -> IN_PROGRESS")

        # 1. 크롤링 수집 진행
        logger.info(f"🕷️ Playwright 크롤러 실행 중...")
        festivals_data = run_festival_crawler(keyword=keyword, max_pages=max_pages)
        total_crawled = len(festivals_data)
        logger.info(f"📊 크롤링 수집 완료: 총 {total_crawled}개 항목 발견")

        # 2. DB 저장 및 업데이트
        saved_count = 0
        updated_count = 0

        for data in festivals_data:
            existing_festival = (
                db.query(Festival)
                .filter(Festival.title == data["title"], Festival.period == data["period"])
                .first()
            )

            if existing_festival:
                existing_festival.location = data["location"]
                existing_festival.image_url = data["image_url"]
                existing_festival.detail_url = data["detail_url"]
                existing_festival.task_id = task_id
                updated_count += 1
            else:
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
            task.total_count = str(total_crawled)
            db.commit()

        logger.info(
            f"✅ [CRAWL SUCCESS] Task ID: {task_id} | 수집: {total_crawled}개 | 신규 저장: {saved_count}개 | 기존 수정: {updated_count}개"
        )

        return {
            "status": "SUCCESS",
            "total_crawled": total_crawled,
            "new_saved": saved_count,
            "updated": updated_count,
        }

    except Exception as exc:
        db.rollback()
        logger.error(f"❌ [CRAWL ERROR] Task ID: {task_id} 처리 중 예외 발생: {str(exc)}", exc_info=True)
        
        task = db.query(CrawlTask).filter_by(task_id=task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            db.commit()
            logger.warning(f"⚠️ Task {task_id} 상태 변경 -> FAILED")
            
        raise exc
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2)
def crawl_festivals_task(self, task_id: str, keyword: str = "서울", max_pages: int = 10):
    try:
        return run_crawl_process(task_id=task_id, keyword=keyword, max_pages=max_pages)
    except Exception as exc:
        logger.warning(f"🔁 Celery 작업 재시도 중... (현재 시도 횟수: {self.request.retries})")
        raise self.retry(exc=exc, countdown=5)