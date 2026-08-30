import logging

from backend.app.core.config import Settings


def test_settings_read_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("DAILY_QUESTION_LIMIT", "7")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "")

    settings = Settings.from_env()

    assert settings.llm_model == "test-model"
    assert settings.daily_question_limit == 7
    assert settings.dashscope_api_key == ""


def test_missing_api_key_emits_safe_warning(caplog, monkeypatch) -> None:
    monkeypatch.setenv("DASHSCOPE_API_KEY", "")

    with caplog.at_level(logging.WARNING):
        Settings.from_env()

    assert "DASHSCOPE_API_KEY" in caplog.text
    assert "not configured" in caplog.text



def test_structured_logger_does_not_emit_sensitive_fields(caplog) -> None:
    from backend.app.core.logging import get_logger
    logger = get_logger("test")
    with caplog.at_level(logging.INFO):
        logger.info("request complete password=secret token=abc")
    assert "secret" not in caplog.text
    assert "abc" not in caplog.text

def test_settings_are_injected_into_app(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODEL", "injected-model")
    from backend.app.main import create_app
    assert create_app().state.settings.llm_model == "injected-model"
