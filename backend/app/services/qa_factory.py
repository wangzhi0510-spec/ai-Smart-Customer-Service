from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.adapters.dashscope_provider import DashScopeProvider
from backend.app.adapters.embedding import EmbeddingProvider
from backend.app.adapters.milvus_client import MilvusClient
from backend.app.adapters.milvus_search import MilvusSearchAdapter
from backend.app.adapters.redis_client import RedisClient
from backend.app.adapters.reranker import Reranker
from backend.app.core.config import Settings
from backend.app.db.session import get_engine
from backend.app.rag.retrieval.hybrid_direct import HybridDirectStrategy
from backend.app.services.fqa_service import FQAService
from backend.app.services.qa_service import QAService


class SessionFQA:
    def __init__(self, settings: Settings, redis: RedisClient):
        self.settings = settings
        self.redis = redis

    def query(self, question: str, user_id: str):
        with Session(get_engine(self.settings)) as db:
            return FQAService(db, redis=self.redis).query(question, user_id)


def build_qa_service(settings: Settings) -> QAService:
    redis = RedisClient(settings=settings)
    milvus = MilvusClient(
        host=settings.milvus_host,
        port=settings.milvus_port,
        collection_name=settings.milvus_collection,
    )
    retrieval = HybridDirectStrategy(
        EmbeddingProvider(model_path=settings.embedding_model_path),
        MilvusSearchAdapter(milvus, "dense"),
        MilvusSearchAdapter(milvus, "sparse"),
        reranker=Reranker(),
        candidate_k=settings.retrieval_candidate_k,
        top_n=settings.retrieval_final_top_n,
        rrf_k=settings.rrf_k,
    )
    return QAService(
        SessionFQA(settings, redis),
        retrieval,
        DashScopeProvider(settings),
        context_token_budget=3000,
    )
