from celery import Celery
from app.core.config import settings

# Settings 클래스에서 중앙 관리하는 REDIS_URL 사용
celery_app = Celery(
    "festival_crawler",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.crawl_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Seoul",
    enable_utc=True,
)