from __future__ import annotations
import logging
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False, extra="ignore")
    app_name: str = Field("AI Smart Customer Service", validation_alias="APP_NAME")
    app_env: str = Field("development", validation_alias="APP_ENV")
    app_host: str = Field("0.0.0.0", validation_alias="APP_HOST")
    app_port: int = Field(8000, validation_alias="APP_PORT")
    app_cors_origins: list[str] = Field(default_factory=lambda:["http://localhost:5173"], validation_alias="APP_CORS_ORIGINS")
    database_url: str = Field("mysql+pymysql://ai_customer_service:change_me@127.0.0.1:3306/ai_customer_service", validation_alias="DATABASE_URL")
    redis_url: str = Field("redis://127.0.0.1:6379/0", validation_alias="REDIS_URL")
    milvus_host: str = Field("127.0.0.1", validation_alias="MILVUS_HOST")
    milvus_port: int = Field(19530, validation_alias="MILVUS_PORT")
    dashscope_api_key: str = Field("", validation_alias="DASHSCOPE_API_KEY")
    dashscope_base_url: str = Field("https://dashscope.aliyuncs.com/compatible-mode/v1", validation_alias="DASHSCOPE_BASE_URL")
    llm_model: str = Field("qwen-plus", validation_alias="LLM_MODEL")
    jwt_secret_key: str = Field("", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", validation_alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(1440, validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    embedding_model_path: str = Field("", validation_alias="EMBEDDING_MODEL_PATH")
    reranker_model_path: str = Field("", validation_alias="RERANKER_MODEL_PATH")
    max_upload_size_mb: int = Field(20, validation_alias="MAX_UPLOAD_SIZE_MB")
    daily_question_limit: int = Field(100, validation_alias="DAILY_QUESTION_LIMIT")
    max_question_length: int = Field(500, validation_alias="MAX_QUESTION_LENGTH")
    parent_chunk_size: int = Field(1200, validation_alias="PARENT_CHUNK_SIZE")
    child_chunk_size: int = Field(320, validation_alias="CHILD_CHUNK_SIZE")
    chunk_overlap: int = Field(64, validation_alias="CHUNK_OVERLAP")
    retrieval_candidate_k: int = Field(20, validation_alias="RETRIEVAL_CANDIDATE_K")
    retrieval_final_top_n: int = Field(5, validation_alias="RETRIEVAL_FINAL_TOP_N")
    rrf_k: int = Field(60, validation_alias="RRF_K")
    conversation_history_turns: int = Field(5, validation_alias="CONVERSATION_HISTORY_TURNS")
    @classmethod
    def from_env(cls) -> "Settings":
        settings=cls()
        if not settings.dashscope_api_key:
            logging.getLogger("ai_customer_service.config").warning("DASHSCOPE_API_KEY is not configured")
        return settings
