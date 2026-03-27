from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery("inschoolchecker", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task
def discover_sources_job(district_url: str) -> dict:
    return {"status": "queued", "district_url": district_url}


@celery_app.task
def parse_source_job(source_id: str) -> dict:
    return {"status": "queued", "source_id": source_id}


@celery_app.task
def refresh_tracked_district_job(district_id: str) -> dict:
    return {"status": "queued", "district_id": district_id}
