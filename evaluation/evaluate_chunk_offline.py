"""不出网的 chunk 参数预检：切分 + BM25 + 证据锚点指标。

这份结果只能用于发现标注、切分与 BM25 的明显问题，不代替规划中的
vector / hybrid / hybrid_rerank 真实对照。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from evaluation.dataset import EVIDENCE_ANCHORS_PATH, REGRESSION_PATH, prepare_questions
from evaluation.evaluate_retrieval import summarize
from evaluation.metrics import (
    adjacent_chunk_pair_rate,
    complete_evidence_at_k,
    evidence_group_recall,
    hit_rank,
    recall_at_k,
    reciprocal_rank,
    relevant_hit_count,
)
from rag_one.config import PROJECT_ROOT
from rag_one.indexing.bm25_store import B, K1, build_index, search
from rag_one.state import runtime_metadata

CONFIGS = ((600, 150), (800, 150), (1000, 150), (800, 80), (800, 220))
DEFAULT_OUT = PROJECT_ROOT / "data" / "eval" / "results" / "v2.5" / "chunk-offline-bm25.json"


def evaluate_config(chunk_size: int, chunk_overlap: int) -> dict:
    questions, chunks = prepare_questions(
        REGRESSION_PATH,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    build_start = time.perf_counter()
    index = build_index(chunks)
    build_ms = round((time.perf_counter() - build_start) * 1000)
    rows: list[dict] = []
    for question in questions:
        start = time.perf_counter()
        hits = search(question["question"], top_k=10, index=index)
        latency_ms = round((time.perf_counter() - start) * 1000)
        hit_ids = [hit["id"] for hit in hits]
        relevant = question["relevant_chunk_ids"]
        groups = question["evidence_groups"]
        row = {
            "question_id": question["id"],
            "question": question["question"],
            "type": question["type"],
            "relevant_chunk_ids": relevant,
            "evidence_groups": groups,
            "latency_ms": latency_ms,
            "hits": [{"rank": hit["rank"], "chunk_id": hit["id"], "source": hit["source"]} for hit in hits],
            "hit_rank": hit_rank(hit_ids, relevant) if relevant else None,
            "relevant_hit_count": relevant_hit_count(hit_ids, relevant, 10) if relevant else 0,
            "recall_at_5": recall_at_k(hit_ids, relevant, 5) if relevant else None,
            "recall_at_10": recall_at_k(hit_ids, relevant, 10) if relevant else None,
            "reciprocal_rank": round(reciprocal_rank(hit_ids, relevant, 10), 6) if relevant else None,
            "evidence_group_recall_at_5": evidence_group_recall(hit_ids, groups, 5),
            "complete_evidence_at_5": complete_evidence_at_k(hit_ids, groups, 5),
            "adjacent_chunk_pair_rate_at_5": round(adjacent_chunk_pair_rate(hit_ids, 5), 6),
            "distinct_sources_at_5": len({hit["source"] for hit in hits[:5]}),
            "context_chars_at_5": sum(len(hit["text"]) for hit in hits[:5]),
        }
        rows.append(row)
    return {
        "config": {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "chunk_count": len(chunks),
            "avg_chunk_chars": round(sum(len(chunk["text"]) for chunk in chunks) / len(chunks), 1),
            "bm25_term_count": index["meta"]["term_count"],
            "bm25_k1": K1,
            "bm25_b": B,
            "build_ms": build_ms,
        },
        "summary": summarize(rows),
        "questions": rows,
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# Chunk 参数离线 BM25 预检",
        "",
        "> 这是不出网预检，不代替四检索模式真实实验，也不用于解密 holdout。",
        "",
        "| 参数 | chunks | 平均字符 | R@5 | MRR@10 | 证据组@5 | 完整证据@5 | 相邻对 | 来源数 | 上下文字符 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for run in payload["runs"]:
        config = run["config"]
        summary = run["summary"]
        lines.append(
            f"| {config['chunk_size']}/{config['chunk_overlap']} | {config['chunk_count']} | "
            f"{config['avg_chunk_chars']} | {summary['recall_at_5']:.1%} | "
            f"{summary['mrr_at_10']:.3f} | {summary['evidence_group_recall_at_5']:.1%} | "
            f"{summary['complete_evidence_at_5']:.1%} | "
            f"{summary['avg_adjacent_chunk_pair_rate_at_5']:.1%} | "
            f"{summary['avg_distinct_sources_at_5']:.2f} | {summary['avg_context_chars_at_5']:.1f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="chunk 参数离线 BM25 预检")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    out = args.out.resolve()
    md_out = out.with_suffix(".md")
    if (out.exists() or md_out.exists()) and not args.force:
        raise SystemExit(f"结果已存在：{out}（使用 --force 才允许覆盖）")
    payload = {
        "run": {
            "name": "chunk-offline-bm25",
            "scope": "regression-only",
            "dataset_sha256": hashlib.sha256(REGRESSION_PATH.read_bytes()).hexdigest(),
            "evidence_anchors_sha256": hashlib.sha256(EVIDENCE_ANCHORS_PATH.read_bytes()).hexdigest(),
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "runtime": runtime_metadata(),
        },
        "runs": [evaluate_config(size, overlap) for size, overlap in CONFIGS],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
