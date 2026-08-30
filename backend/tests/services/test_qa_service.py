from backend.app.rag.retrieval.contracts import ContextDocument, RetrievalResult
from backend.app.services.qa_service import QAService, QAResult


class FakeFQA:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def query(self, question, user_id):
        self.calls += 1
        return self.result


class FakeRetrieval:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def retrieve(self, question, user_id, source_filter=None):
        self.calls += 1
        return self.result


class FakeLLM:
    def complete(self, messages):
        return "根据资料，7天内可退款。"


def test_fqa_hit_short_circuits_llm_and_returns_uniform_result():
    fqa = FakeFQA(type("FQA", (), {"matched": True, "answer": "标准答案", "entry_id": "f1", "score": 1.0})())
    retrieval = FakeRetrieval(RetrievalResult([]))

    result = QAService(fqa=fqa, retrieval=retrieval, llm=FakeLLM()).answer("退款", "s1", "u1")

    assert isinstance(result, QAResult)
    assert result.answer == "标准答案"
    assert result.answer_type == "fqa"
    assert result.sources == []
    assert retrieval.calls == 0


def test_rag_answer_uses_context_and_returns_sources():
    context = ContextDocument("p1", "7天内可退款", "guide.txt", 2, "退款", .9, "doc-1", 1)
    retrieval = FakeRetrieval(RetrievalResult([context]))
    fqa = FakeFQA(type("FQA", (), {"matched": False, "answer": None, "entry_id": None, "score": 0.0})())

    result = QAService(fqa=fqa, retrieval=retrieval, llm=FakeLLM()).answer("如何退款", "s1", "u1")

    assert result.answer == "根据资料，7天内可退款。"
    assert result.answer_type == "rag"
    assert result.retrieval_strategy == "hybrid_direct"
    assert result.sources[0]["document_id"] == "doc-1"


def test_no_evidence_returns_controlled_fallback_without_calling_llm():
    fqa = FakeFQA(type("FQA", (), {"matched": False, "answer": None, "entry_id": None, "score": 0.0})())
    retrieval = FakeRetrieval(RetrievalResult([]))
    llm = type("LLM", (), {"complete": lambda self, messages: (_ for _ in ()).throw(AssertionError())})()

    result = QAService(fqa=fqa, retrieval=retrieval, llm=llm).answer("未知", "s1", "u1")

    assert result.answer_type == "fallback"
    assert "知识库" in result.answer
