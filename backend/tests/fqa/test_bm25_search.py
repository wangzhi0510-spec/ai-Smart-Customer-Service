from backend.app.fqa.bm25_search import BM25Search


def test_bm25_returns_relevant_entry_and_score():
    search = BM25Search(
        [
            {"id": "1", "question": "如何申请退款", "answer": "订单支付后七天内可申请退款"},
            {"id": "2", "question": "如何修改收货地址", "answer": "发货前可以修改地址"},
        ]
    )

    result = search.search("申请退款", top_k=1)

    assert result[0]["id"] == "1"
    assert result[0]["score"] > 0
