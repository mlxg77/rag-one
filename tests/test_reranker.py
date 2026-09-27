"""重排链路单元测试：reranker 打分编排 + hybrid_reranker 组合与回退。

全程离线：Rerank API 用假分数替身，hybrid_search 用构造的融合结果替身。

运行：python -X utf8 -m pytest tests/test_reranker.py -v
"""

import pytest

from src import hybrid_reranker, reranker
from src.reranker import RerankError


def make_candidates() -> list[dict]:
    """构造三条与 hybrid_search 输出同构的融合候选（rank 1~3 为融合名次）。"""
    return [
        {
            "id": "c-1", "source": "a.md", "page": None, "text": "文本一",
            "score": 0.032, "rank": 1, "vector_rank": 1, "bm25_rank": 4,
        },
        {
            "id": "c-2", "source": "b.md", "page": None, "text": "文本二",
            "score": 0.030, "rank": 2, "vector_rank": 5, "bm25_rank": 1,
        },
        {
            "id": "c-3", "source": "c.md", "page": None, "text": "文本三",
            "score": 0.028, "rank": 3, "vector_rank": None, "bm25_rank": 2,
        },
    ]


def fake_scores(scores: list[float]):
    """返回一个替身 _call_rerank_api：忽略入参，固定返回给定分数。"""

    def _fake(question: str, texts: list[str]) -> list[float]:
        return scores

    return _fake


def fail_api(question: str, texts: list[str]) -> list[float]:
    """替身：模拟 Rerank API 失败。"""
    raise RerankError("模拟接口失败")


def test_rerank_reorders_and_writes_fields(monkeypatch):
    # 假分数 [c-2 最高] → 重排后 c-2 第一；rerank_score 写入；原字段保留；rank 重写为 1 起
    monkeypatch.setattr(reranker, "_call_rerank_api", fake_scores([0.1, 0.9, 0.5]))
    candidates = make_candidates()
    hits = reranker.rerank("问", candidates, top_k=3)
    assert [h["id"] for h in hits] == ["c-2", "c-3", "c-1"]
    assert [h["rank"] for h in hits] == [1, 2, 3]
    assert hits[0]["rerank_score"] == 0.9
    assert hits[0]["vector_rank"] == 5   # 原字段原样保留
    assert hits[0]["bm25_rank"] == 1
    assert candidates[0]["rank"] == 1    # 传入的候选不被修改（副本上操作）


def test_rerank_tie_keeps_input_order(monkeypatch):
    # 分数并列 → 保持输入（融合）顺序，不在平局时乱动上游共识序
    monkeypatch.setattr(reranker, "_call_rerank_api", fake_scores([0.5, 0.5, 0.1]))
    hits = reranker.rerank("问", make_candidates(), top_k=3)
    assert [h["id"] for h in hits] == ["c-1", "c-2", "c-3"]


def test_rerank_truncates_to_top_k(monkeypatch):
    monkeypatch.setattr(reranker, "_call_rerank_api", fake_scores([0.1, 0.9, 0.5]))
    hits = reranker.rerank("问", make_candidates(), top_k=2)
    assert [h["id"] for h in hits] == ["c-2", "c-3"]


def test_rerank_fewer_candidates_than_top_k(monkeypatch):
    # 候选不足 top_k：有多少返回多少，不报错（候选不足时正常工作）
    monkeypatch.setattr(reranker, "_call_rerank_api", fake_scores([0.9, 0.1]))
    hits = reranker.rerank("问", make_candidates()[:2], top_k=5)
    assert len(hits) == 2


def test_rerank_empty_candidates_short_circuits(monkeypatch):
    # 空候选直接返回 []（API 实测不接受空列表），且不发请求
    def boom(question: str, texts: list[str]) -> list[float]:
        raise AssertionError("空候选不应调用 Rerank API")

    monkeypatch.setattr(reranker, "_call_rerank_api", boom)
    assert reranker.rerank("问", [], top_k=5) == []


def test_rerank_api_failure_raises(monkeypatch):
    # API 失败 → 抛 RerankError（reranker 层不吞错）
    monkeypatch.setattr(reranker, "_call_rerank_api", fail_api)
    with pytest.raises(RerankError):
        reranker.rerank("问", make_candidates(), top_k=3)


def test_hybrid_rerank_records_rrf_rank(monkeypatch):
    # 组合链路：rrf_rank 留档重排前名次；rank 是重排后名次
    monkeypatch.setattr(hybrid_reranker, "hybrid_search", lambda q, top_k: make_candidates())
    monkeypatch.setattr(reranker, "_call_rerank_api", fake_scores([0.1, 0.9, 0.5]))
    hits = hybrid_reranker.hybrid_rerank_search("问", top_k=3)
    by_id = {h["id"]: h for h in hits}
    assert by_id["c-2"]["rank"] == 1 and by_id["c-2"]["rrf_rank"] == 2  # 2 → 1 上升
    assert by_id["c-1"]["rank"] == 3 and by_id["c-1"]["rrf_rank"] == 1  # 1 → 3 下降
    assert all("rerank_score" in h for h in hits)


def test_hybrid_rerank_falls_back_on_failure(monkeypatch, capsys):
    # API 失败 + fallback=True → 回退融合 Top-K：字段齐全、无 rerank_score、打印警告
    monkeypatch.setattr(hybrid_reranker, "hybrid_search", lambda q, top_k: make_candidates())
    monkeypatch.setattr(reranker, "_call_rerank_api", fail_api)
    hits = hybrid_reranker.hybrid_rerank_search("问", top_k=2)
    assert [h["id"] for h in hits] == ["c-1", "c-2"]     # 融合原顺序
    assert all(h["rrf_rank"] == h["rank"] for h in hits)  # 未重排，名次即融合名次
    assert all("rerank_score" not in h for h in hits)
    assert "回退" in capsys.readouterr().out


def test_hybrid_rerank_strict_mode_raises(monkeypatch):
    # fallback=False → 失败直接抛错，不返回半截结果
    monkeypatch.setattr(hybrid_reranker, "hybrid_search", lambda q, top_k: make_candidates())
    monkeypatch.setattr(reranker, "_call_rerank_api", fail_api)
    with pytest.raises(RerankError):
        hybrid_reranker.hybrid_rerank_search("问", top_k=3, fallback=False)
