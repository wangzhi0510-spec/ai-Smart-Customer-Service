from backend.app.workers import document_tasks
from backend.app.workers.celery_app import celery_app


def test_document_processing_task_is_registered_when_worker_starts():
    assert 'backend.app.workers.document_tasks.process_document' in celery_app.tasks


def test_document_processing_task_returns_json_serializable_result(monkeypatch):
    monkeypatch.setattr(
        document_tasks,
        'process_document',
        lambda document_id: document_tasks.DocumentTaskResult(document_id, 'ready', 2),
    )

    result = document_tasks.process_document_task.run('doc-1')

    assert result == {'document_id': 'doc-1', 'status': 'ready', 'chunk_count': 2, 'error_code': None}
