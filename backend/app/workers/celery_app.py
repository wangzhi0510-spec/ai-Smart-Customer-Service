from celery import Celery

from backend.app.core.config import Settings

settings = Settings.from_env()
celery_app = Celery("ai_customer_service", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_routes = {"backend.app.workers.document_tasks.process_document": {"queue": "documents"}}
celery_app.conf.task_default_queue = "documents"
