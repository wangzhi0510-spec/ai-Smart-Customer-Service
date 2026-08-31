from celery import Celery

from backend.app.core.config import Settings

settings = Settings.from_env()
celery_app = Celery(
    "ai_customer_service",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.task_routes = {"backend.app.workers.document_tasks.process_document": {"queue": "documents"}}
celery_app.conf.task_default_queue = "documents"

# Import task definitions during app initialization so API tests and worker startup share the same registry.
from backend.app.workers import document_tasks as _document_tasks  # noqa: F401
