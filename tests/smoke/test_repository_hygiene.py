from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def git_check_ignore(*paths: str) -> set[str]:
    result = subprocess.run(
        ["git", "check-ignore", "-z", "--stdin"],
        cwd=ROOT,
        input=("\0".join(paths) + "\0").encode(),
        capture_output=True,
        check=False,
    )
    return {
        item.decode().replace("\\", "/")
        for item in result.stdout.split(b"\0")
        if item
    }


def parse_env_template(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        assert separator, f"环境变量行缺少等号: {raw_line}"
        values[key.strip()] = value.strip()
    return values


def test_sensitive_and_generated_paths_are_ignored() -> None:
    ignored_paths = {
        ".env",
        ".env.local",
        ".venv/Scripts/python.exe",
        "backend/storage/documents/example.pdf",
        "backend/logs/app.log",
        "backend/models/bge-m3/model.safetensors",
        "frontend/node_modules/vue/package.json",
        "frontend/dist/index.html",
        "backend/.pytest_cache/README.md",
        "backend/app/__pycache__/main.cpython-312.pyc",
    }

    assert git_check_ignore(*sorted(ignored_paths)) == ignored_paths


def test_public_environment_template_has_safe_required_settings() -> None:
    template = ROOT / ".env.example"
    values = parse_env_template(template)

    required_keys = {
        "APP_ENV",
        "DATABASE_URL",
        "REDIS_URL",
        "MILVUS_HOST",
        "MILVUS_PORT",
        "DASHSCOPE_API_KEY",
        "LLM_MODEL",
        "JWT_SECRET_KEY",
        "EMBEDDING_MODEL_PATH",
        "RERANKER_MODEL_PATH",
        "DAILY_QUESTION_LIMIT",
        "MAX_QUESTION_LENGTH",
        "MAX_UPLOAD_SIZE_MB",
    }

    assert required_keys <= values.keys()
    assert values["DASHSCOPE_API_KEY"] == ""
    assert values["JWT_SECRET_KEY"] == ""
    assert values["LLM_MODEL"] == "qwen-plus"
    assert values["DAILY_QUESTION_LIMIT"] == "100"
    assert values["MAX_QUESTION_LENGTH"] == "500"


def test_public_environment_template_is_not_ignored() -> None:
    assert ".env.example" not in git_check_ignore(".env.example")

def test_backend_model_source_code_is_not_ignored() -> None:
    assert "backend/app/models/user.py" not in git_check_ignore("backend/app/models/user.py")
