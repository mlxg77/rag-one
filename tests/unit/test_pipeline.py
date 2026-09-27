"""四链路追踪层单元测试：分发 / 分段计时 / 候选池 / 回退。全程离线（底层全部替身）。

运行：python -X utf8 -m pytest tests/unit/test_pipeline.py -v
"""

import pytest

from rag_one import pipeline
from rag_one.retrieval import reranker
from rag_one.retrieval.reranker import RerankError


def make_hits(prefix: str, n: int) -> list[dict]:
    """构造与检索输出同构的命中（rank 1..n，text 供重排替身使用）。"""
    return [
        {
            "rank": i,
            "id": f"{prefix}-{i}",
            "score": 1.0 / i,
            "source": f"{prefix}.md",
            "page": None,
            "text": f"{prefix} 文本 {i}",
        }
        for i in range(1, n + 1)
    ]


def fake_generate(question, hits):
    return {"answer": f"回答（{len(hits)} 条）", "usage": {"prompt_tokens": 100, "completion_tokens": 10}}


@pytest.fixture(autouse=True)
def patch_generate(monkeypatch):
    """所有用例都不真调 LLM。"""
    monkeypatch.setattr(pipeline, "generate_answer", fake_generate)


def test_vector_mode_trace(monkeypatch):
    monkeypatch.setattr(pipeline, "retrieve", lambda q, top_k: make_hits("v", top_k))
    out = pipeline.run_chain("vector", "问", top_k=3)
    assert [s["name"] for s in out["stages"]] == ["向量召回", "答案生成"]
    assert len(out["hits"]) == 3
    assert [c["final_rank"] for c in out["candidates"]] == [1, 2, 3]
    assert out["answer"] == "回答（3 条）"
    assert out["rerank_tokens"] is None and out["warnings"] == []


def test_bm25_mode_trace(monkeypatch):
    monkeypatch.setattr(pipeline, "bm25_search", lambda q, top_k: make_hits("b", top_k))
    out = pipeline.run_chain("bm25", "问", top_k=2)
    assert [s["name"] for s in out["stages"]] == ["BM25 召回", "答案生成"]
    assert len(out["hits"]) == 2


def test_hybrid_mode_fuses_and_truncates(monkeypatch):
    monkeypatch.setattr(pipeline, "retrieve", lambda q, top_k: make_hits("v", top_k))
    monkeypatch.setattr(pipeline, "bm25_search", lambda q, top_k: make_hits("b", top_k))
    out = pipeline.run_chain("hybrid", "问", top_k=2, vector_k=4, bm25_k=4, candidate_k=6)
    assert [s["name"] for s in out["stages"]] == ["向量召回", "BM25 召回", "RRF 融合", "答案生成"]
    assert out["stages"][2]["count"] == 6            # 融合候选全表
    assert len(out["hits"]) == 2                     # 进 Prompt 只 2 条
    assert all("vector_rank" in c and "bm25_rank" in c for c in out["candidates"])
    assert sum(1 for c in out["candidates"] if c["final_rank"]) == 2
    assert [c["final_rank"] for c in out["candidates"]][:2] == [1, 2]  # 截头部，名次不变


def test_hybrid_rerank_full_scores_and_order(monkeypatch):
    monkeypatch.setattr(pipeline, "retrieve", lambda q, top_k: make_hits("v", top_k))
    monkeypatch.setattr(pipeline, "bm25_search", lambda q, top_k: make_hits("b", top_k))

    def fake_api(question, texts):
        # 反向打分：融合顺序的第一条最低分——保证重排后顺序有明显变化
        return [0.1 * (len(texts) - i) for i in range(len(texts))]

    monkeypatch.setattr(reranker, "_call_rerank_api", fake_api)
    out = pipeline.run_chain("hybrid_rerank", "问", top_k=2, vector_k=4, bm25_k=4, candidate_k=6)
    assert [s["name"] for s in out["stages"]] == ["向量召回", "BM25 召回", "RRF 融合", "Reranker 精排", "答案生成"]
    assert len(out["candidates"]) == 6               # 全量候选都在
    assert all("rerank_score" in c for c in out["candidates"])  # 全量重排分（不止 Top-K）
    assert all("rrf_rank" in c for c in out["candidates"])
    scores = [c["rerank_score"] for c in out["candidates"]]
    assert scores == sorted(scores, reverse=True)    # 按重排分降序
    assert len(out["hits"]) == 2
    assert [h["final_rank"] for h in out["hits"]] == [1, 2]


def test_hybrid_rerank_fallback(monkeypatch):
    monkeypatch.setattr(pipeline, "retrieve", lambda q, top_k: make_hits("v", top_k))
    monkeypatch.setattr(pipeline, "bm25_search", lambda q, top_k: make_hits("b", top_k))

    def fail_api(question, texts):
        raise RerankError("模拟接口失败")

    monkeypatch.setattr(reranker, "_call_rerank_api", fail_api)
    out = pipeline.run_chain("hybrid_rerank", "问", top_k=3, candidate_k=5)
    assert out["warnings"] and "回退" in out["warnings"][0]
    assert len(out["hits"]) == 3
    assert all("rerank_score" not in c for c in out["candidates"])   # 回退：无重排分
    assert all(c["rrf_rank"] == c["rank"] for c in out["candidates"])  # 名次即融合名次


def test_hybrid_rerank_strict_mode_raises(monkeypatch):
    monkeypatch.setattr(pipeline, "retrieve", lambda q, top_k: make_hits("v", top_k))
    monkeypatch.setattr(pipeline, "bm25_search", lambda q, top_k: make_hits("b", top_k))

    def fail_api(question, texts):
        raise RerankError("模拟接口失败")

    monkeypatch.setattr(reranker, "_call_rerank_api", fail_api)
    with pytest.raises(RerankError):
        pipeline.run_chain("hybrid_rerank", "问", fallback=False)


def test_unknown_mode_raises():
    with pytest.raises(ValueError, match="未知检索模式"):
        pipeline.run_chain("bogus", "问")


def test_empty_question_rejected_before_retrieval():
    with pytest.raises(ValueError, match="question 不能为空"):
        pipeline.run_chain("vector", "  ")
