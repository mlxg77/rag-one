"""BM25 核心逻辑单元测试：离线、不依赖网络与真实索引（用构造语料）。

运行：python -X utf8 -m pytest tests/unit/test_bm25.py -v
"""

import json
import os

import pytest

from rag_one.indexing.bm25_store import build_index, save_index, search

CHUNKS = [
    {
        "id": "doc-a.md:chunk-0",
        "text": "差旅住宿标准：去上海出差，酒店每晚含税最高报销 700 元。",
        "metadata": {"source": "doc-a.md", "chunk_index": 0},
    },
    {
        "id": "doc-a.md:chunk-1",
        "text": "报销须在事项结束后三十个自然日内提交。",
        "metadata": {"source": "doc-a.md", "chunk_index": 1},
    },
    {
        "id": "doc-b.md:chunk-0",
        "text": "远程办公申请需要直属主管审批。",
        "metadata": {"source": "doc-b.md", "chunk_index": 0},
    },
    {
        "id": "doc-c.md:chunk-0",
        "text": "远程办公申请需要直属主管审批。",  # 与 doc-b 完全相同：制造相同分数
        "metadata": {"source": "doc-c.md", "chunk_index": 0},
    },
]

INDEX = build_index(CHUNKS)


def test_empty_query_returns_empty():
    assert search("   ", top_k=3, index=INDEX) == []


def test_unknown_term_returns_empty():
    assert search("量子纠缠", top_k=3, index=INDEX) == []


def test_repeated_terms_same_as_single():
    once = search("报销", top_k=3, index=INDEX)
    thrice = search("报销 报销 报销", top_k=3, index=INDEX)
    assert [h["id"] for h in once] == [h["id"] for h in thrice]
    assert once[0]["score"] == pytest.approx(thrice[0]["score"])


def test_tied_scores_break_by_id():
    hits = search("远程办公 审批", top_k=3, index=INDEX)
    assert len(hits) == 2
    # doc-b 与 doc-c 文本相同 → 分数并列，按 id 升序兜底
    assert hits[0]["id"] == "doc-b.md:chunk-0"
    assert hits[1]["id"] == "doc-c.md:chunk-0"
    assert hits[0]["score"] == pytest.approx(hits[1]["score"])


def test_top_k_boundary():
    # 超过命中数：返回全部（这里 2 条）
    assert len(search("远程办公 审批", top_k=99, index=INDEX)) == 2
    # 恰好截断
    assert len(search("远程办公 审批", top_k=1, index=INDEX)) == 1
    # 非法边界：显式报错
    with pytest.raises(ValueError):
        search("报销", top_k=0, index=INDEX)


def test_result_fields_and_order():
    hits = search("报销", top_k=3, index=INDEX)
    assert hits, "预期至少 1 条命中"
    for i, hit in enumerate(hits, start=1):
        assert hit["rank"] == i
        assert set(hit) >= {"rank", "id", "score", "source", "page", "text"}
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_save_index_atomic_no_tmp_left(tmp_path):
    # 原子写：替换后无 .tmp 残留，内容完整可读
    path = tmp_path / "index.json"
    save_index(INDEX, path)
    assert path.exists()
    assert not (tmp_path / "index.json.tmp").exists()
    assert json.loads(path.read_text(encoding="utf-8"))["meta"]["chunk_count"] == len(CHUNKS)


def test_save_index_failure_keeps_old_file(tmp_path, monkeypatch):
    # 替换失败（模拟写出中断）：旧文件原封不动，新内容只落在 .tmp
    path = tmp_path / "index.json"
    save_index(INDEX, path)
    before = path.read_text(encoding="utf-8")

    def boom(src, dst):
        raise OSError("模拟替换失败")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        save_index({**INDEX, "avgdl": 0.0}, path)
    assert path.read_text(encoding="utf-8") == before
