"""RAG 组装单元测试：检索与生成的结果透传（全替身，离线）。

运行：python -X utf8 -m pytest tests/unit/test_rag.py -v
"""

import pytest

from rag_one import rag
from rag_one.retrieval.vector import DEFAULT_TOP_K


def test_ask_assembles_retrieve_and_generate(monkeypatch):
    hits = [{"rank": 1, "id": "a", "score": 0.9, "source": "a.md", "page": None, "text": "T"}]
    calls: dict = {}

    def fake_retrieve(question, top_k):
        calls["question"] = question
        calls["top_k"] = top_k
        return hits

    def fake_generate(question, got_hits):
        calls["gen_question"] = question
        calls["gen_hits"] = got_hits
        return {"answer": "答案", "usage": {"prompt_tokens": 10, "completion_tokens": 2}}

    monkeypatch.setattr(rag, "retrieve", fake_retrieve)
    monkeypatch.setattr(rag, "generate_answer", fake_generate)

    out = rag.ask("问题？", top_k=3)

    assert out == {
        "question": "问题？",
        "hits": hits,
        "answer": "答案",
        "usage": {"prompt_tokens": 10, "completion_tokens": 2},
        "prompt_version": None,
        "citation_validation": None,
    }
    # 检索拿到问题与 top_k；生成拿到同一份 hits
    assert calls == {
        "question": "问题？",
        "top_k": 3,
        "gen_question": "问题？",
        "gen_hits": hits,
    }


def test_ask_uses_default_top_k(monkeypatch):
    seen: dict = {}

    def fake_retrieve(question, top_k):
        seen["top_k"] = top_k
        return []

    monkeypatch.setattr(rag, "retrieve", fake_retrieve)
    monkeypatch.setattr(rag, "generate_answer", lambda q, h: {"answer": "", "usage": {}})

    rag.ask("问题？")
    assert seen["top_k"] == DEFAULT_TOP_K


def test_ask_rejects_empty_question():
    with pytest.raises(ValueError, match="question 不能为空"):
        rag.ask("\t")
