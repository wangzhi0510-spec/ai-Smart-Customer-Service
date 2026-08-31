from backend.app.main import create_app


def test_create_app_provisions_real_qa_service_by_default(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'sqlite+pysqlite:///:memory:')
    monkeypatch.setenv('DASHSCOPE_API_KEY', 'test-key')
    app = create_app()

    assert app.state.qa_service.__class__.__name__ == 'QAService'
    assert app.state.qa_service.fqa.__class__.__name__ == 'SessionFQA'
    assert app.state.qa_service.llm.__class__.__name__ == 'DashScopeProvider'

