from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def load_compose() -> dict:
    compose_path = ROOT.parent / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist"
    return yaml.safe_load(compose_path.read_text(encoding="utf-8"))


def test_compose_defines_infrastructure_services_and_named_volumes() -> None:
    compose = load_compose()
    services = compose["services"]
    for name in ("mysql", "redis", "etcd", "minio", "milvus"):
        assert name in services
        assert "healthcheck" in services[name]
    assert {"mysql_data", "redis_data", "milvus_data", "etcd_data", "minio_data"}.issubset(
        compose["volumes"]
    )
    assert "app-network" in compose["networks"]


def test_compose_app_profile_contains_backend_worker_frontend() -> None:
    services = load_compose()["services"]
    for name in ("backend", "worker", "frontend"):
        assert name in services
        assert "app" in services[name].get("profiles", [])


def test_app_images_use_non_root_and_mount_models_and_documents() -> None:
    services = load_compose()["services"]
    for name in ("backend", "worker"):
        service = services[name]
        assert service.get("user") not in (None, "root", 0)
        mounts = "\n".join(str(item) for item in service.get("volumes", []))
        assert "models" in mounts
        assert "documents" in mounts

    backend_dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    frontend_dockerfile = (ROOT.parent / "frontend" / "Dockerfile").read_text(encoding="utf-8")
    assert "USER 10001:10001" in backend_dockerfile
    assert "USER 101" in frontend_dockerfile


def test_backend_runs_migrations_and_frontend_proxies_api() -> None:
    services = load_compose()["services"]
    assert "alembic upgrade head" in services["backend"]["command"]
    nginx_config = (ROOT.parent / "frontend" / "nginx.conf").read_text(encoding="utf-8")
    assert "proxy_pass http://backend:8000" in nginx_config
    assert "proxy_buffering off" in nginx_config
    assert "client_max_body_size 20m" in nginx_config.lower()
    healthcheck = services["frontend"]["healthcheck"]["test"]
    assert "http://127.0.0.1:8080/" in str(healthcheck)


def test_compose_preserves_nested_model_mount_paths() -> None:
    services = load_compose()["services"]
    environment = services["backend"].get("environment", {})

    assert environment["EMBEDDING_MODEL_PATH"] == "/models/embedding/bge-m3"
    assert environment["RERANKER_MODEL_PATH"] == "/models/reranker/bge-reranker-large"


def test_backend_image_installs_local_embedding_runtime() -> None:
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    backend_dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "flagembedding" in requirements
    assert "PYTHONPATH=/app" in backend_dockerfile
    assert "https://download.pytorch.org/whl/cpu" in backend_dockerfile
    assert "chown -R 10001:10001 /app/backend/storage" in backend_dockerfile


def test_compose_ports_match_env_example() -> None:
    compose = load_compose()
    env_text = (ROOT.parent / ".env.example").read_text(encoding="utf-8")
    assert "APP_PORT=8000" in env_text
    assert "${MYSQL_PORT:-3306}:3306" in compose["services"]["mysql"]["ports"]
    assert "${REDIS_PORT:-6379}:6379" in compose["services"]["redis"]["ports"]
    assert "${MILVUS_PORT:-19530}:19530" in compose["services"]["milvus"]["ports"]


def test_mysql_init_enforces_declared_utf8mb4_collation() -> None:
    init_sql = (ROOT.parent / "docker" / "mysql" / "init.sql").read_text(encoding="utf-8").lower()

    assert "alter database ai_customer_service" in init_sql
    assert "collate utf8mb4_unicode_ci" in init_sql


def test_env_example_leaves_all_secret_values_empty() -> None:
    env_text = (ROOT.parent / ".env.example").read_text(encoding="utf-8")
    values: dict[str, str] = {}
    for raw_line in env_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        assert separator
        values[key.strip()] = value.strip()

    for key in (
        "MYSQL_ROOT_PASSWORD",
        "MYSQL_PASSWORD",
        "MINIO_ROOT_PASSWORD",
        "DASHSCOPE_API_KEY",
        "JWT_SECRET_KEY",
    ):
        assert values[key] == ""

    assert "change_me" not in values["DATABASE_URL"]
