from uuid import uuid4

from backend.app.rag.retrieval.contracts import ContextDocument, SearchHit
from backend.app.rag.retrieval.hybrid_direct import HybridDirectStrategy
from backend.app.rag.retrieval.parent_recovery import recover_parents
from backend.app.rag.retrieval.rrf import rrf_fuse
from backend.app.adapters.reranker import Reranker


def hit(identifier, score, parent, source="guide.txt", active=True, version=1):
    return SearchHit(
        id=identifier, score=score, user_id="user-1", document_id="doc-1", version=version,
        parent_id=parent, child_text=identifier + " text", parent_text="parent " + parent,
        source_name=source, page_number=2, section_title="退款", active_version=active,
    )


def test_rrf_common_hit_ranks_above_single_source_hit():
    fused = rrf_fuse([hit("both", .8, "p1"), hit("dense", .7, "p2")], [hit("both", .6, "p1"), hit("sparse", .9, "p3")], 60)

    assert [item.id for item in fused][0] == "both"


def test_parent_recovery_groups_children_and_preserves_source_metadata():
    contexts = recover_parents([hit("c1", .8, "p1"), hit("c2", .7, "p1"), hit("c3", .9, "p2")])

    assert [item.parent_id for item in contexts] == ["p1", "p2"]
    assert "c1 text" in contexts[0].text and "c2 text" in contexts[0].text
    assert contexts[0].source_name == "guide.txt"


class FakeSearch:
    def __init__(self, values):
        self.values = values
        self.calls = []

    def search(self, embedding, *, user_id, source_filter, limit):
        self.calls.append((embedding, user_id, source_filter, limit))
        return self.values


class FakeEmbedding:
    def embed(self, texts):
        return type("Batch", (), {"dense": [[1.0]], "sparse": [{"refund": 1.0}]})()


def test_hybrid_strategy_filters_user_active_version_and_source_on_both_paths():
    dense = FakeSearch([hit("ok", .9, "p1"), hit("old", .99, "p2", active=False), hit("other", .99, "p3", source="other.md")])
    sparse = FakeSearch([hit("ok", .8, "p1"), hit("old", .99, "p2", active=False)])

    result = HybridDirectStrategy(FakeEmbedding(), dense, sparse, top_n=5).retrieve("退款", "user-1", ["guide.txt"])

    assert [context.parent_id for context in result.contexts] == ["p1"]
    assert dense.calls[0][2] == ["guide.txt"]
    assert sparse.calls[0][2] == ["guide.txt"]


def test_reranker_mock_reorders_and_unavailable_falls_back_with_warning():
    contexts = [ContextDocument("p1", "one", "guide.txt", 1, "退款", .2), ContextDocument("p2", "two", "guide.txt", 2, "退款", .8)]
    ranked = Reranker(backend=lambda question, items: list(reversed(items))).rank("退款", contexts)
    fallback_reranker = Reranker()
    fallback = fallback_reranker.rank("退款", contexts)

    assert [item.parent_id for item in ranked] == ["p2", "p1"]
    assert [item.parent_id for item in fallback] == ["p1", "p2"]
    assert fallback_reranker.last_warning == "RERANKER_UNAVAILABLE"




