from backend.app.workers.celery_app import celery_app


def test_document_processing_task_is_registered_when_worker_starts():
    assert 'backend.app.workers.document_tasks.process_document' in celery_app.tasks
