"""RRF 融合核心逻辑单元测试：离线、纯构造数据（不读索引、不碰网络）。

运行：python -X utf8 -m pytest tests/unit/test_fusion.py -v
"""

import pytest

from rag_one.retrieval.fusion import RRF_K, rrf_fuse


def make_hit(chunk_id: str, rank: int, score: float = 1.0) -> dict:
    """构造一条与 retrieve / bm25 search 同构的命中。"""
    return {
        "rank": rank,
        "id": chunk_id,
        "score": score,
        "source": chunk_id.split(":")[0],
        "page": None,
        "text": f"{chunk_id} 的正文",
    }


def test_same_chunk_merged_by_id():
    # 同一 chunk 两路都命中 → 去重为一条，分数为两路贡献之和
    vector = [make_hit("doc.md:chunk-0", rank=1)]
    bm25 = [make_hit("doc.md:chunk-0", rank=3)]
    fused = rrf_fuse({"vector": vector, "bm25": bm25}, top_k=10)
    assert len(fused) == 1
    assert fused[0]["score"] == pytest.approx(1 / (RRF_K + 1) + 1 / (RRF_K + 3))
    assert fused[0]["vector_rank"] == 1
    assert fused[0]["bm25_rank"] == 3
    assert fused[0]["vector_score"] == 1.0
    assert fused[0]["bm25_score"] == 1.0


def test_single_path_chunk_kept_with_none():
    # 只在单路命中的 chunk 不丢弃；另一路字段显式 None
    vector = [make_hit("v.md:chunk-0", rank=1)]
    bm25 = [make_hit("b.md:chunk-0", rank=1)]
    fused = rrf_fuse({"vector": vector, "bm25": bm25}, top_k=10)
    assert len(fused) == 2
    by_id = {h["id"]: h for h in fused}
    assert by_id["v.md:chunk-0"]["bm25_rank"] is None
    assert by_id["v.md:chunk-0"]["bm25_score"] is None
    assert by_id["b.md:chunk-0"]["vector_rank"] is None


def test_consensus_beats_single_path_top_rank():
    # both：两路各排第 5（2/65 ≈ 0.0308）；single：仅向量路第 1（1/61 ≈ 0.0164）
    # 结论：两路共识 > 单路第一——RRF 的核心价值
    vector = [make_hit("single.md:chunk-0", rank=1), make_hit("both.md:chunk-0", rank=5)]
    bm25 = [make_hit("both.md:chunk-0", rank=5)]
    fused = rrf_fuse({"vector": vector, "bm25": bm25}, top_k=10)
    assert fused[0]["id"] == "both.md:chunk-0"


def test_tie_break_by_id():
    # 对称分布：两 chunk 总分相同 → 按 id 升序兜底
    vector = [make_hit("y.md:chunk-0", rank=1), make_hit("x.md:chunk-0", rank=2)]
    bm25 = [make_hit("x.md:chunk-0", rank=1), make_hit("y.md:chunk-0", rank=2)]
    fused = rrf_fuse({"vector": vector, "bm25": bm25}, top_k=10)
    assert [h["id"] for h in fused] == ["x.md:chunk-0", "y.md:chunk-0"]
    assert fused[0]["score"] == pytest.approx(fused[1]["score"])


def test_rank_and_score_recomputable():
    # 单路单条命中：分数 = 1/(k+rank)，可人工复算；rank 从 1 连续
    vector = [make_hit("a.md:chunk-0", rank=2), make_hit("b.md:chunk-0", rank=4)]
    fused = rrf_fuse({"vector": vector}, top_k=1)
    assert len(fused) == 1
    assert fused[0]["id"] == "a.md:chunk-0"
    assert fused[0]["rank"] == 1
    assert fused[0]["score"] == pytest.approx(1 / (RRF_K + 2))


def test_empty_and_boundary():
    # 空输入 → 空结果；top_k 非法 → 显式报错
    assert rrf_fuse({"vector": [], "bm25": []}, top_k=10) == []
    with pytest.raises(ValueError):
        rrf_fuse({"vector": []}, top_k=0)
