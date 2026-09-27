"""四种检索模式的可复现评估，输出 JSON 与 Markdown。"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from evaluation.dataset import (
    EVIDENCE_ANCHORS_PATH,
    REGRESSION_PATH,
    evidence_groups_of,
    prepare_questions,
)
from evaluation.metrics import (
    complete_evidence_at_k,
    adjacent_chunk_pair_rate,
    evidence_group_recall,
    hit_rank,
    percentile,
    recall_at_k,
    reciprocal_rank,
    relevant_hit_count,
)
from rag_one.config import LLM_MODEL, RERANK_MODEL
from rag_one.generation.generator import LLM_TEMPERATURE, PROMPT_VERSION
from rag_one.indexing.bm25_store import B, K1, search as bm25_search
from rag_one.retrieval.fusion import RRF_K
from rag_one.retrieval.hybrid import BM25_CANDIDATES, VECTOR_CANDIDATES, hybrid_search
from rag_one.retrieval.hybrid_reranker import RERANK_CANDIDATES, hybrid_rerank_search
from rag_one.retrieval.vector import retrieve
from rag_one.state import verify_project_state

DEFAULT_RESULTS_DIR = Path("data/eval/results/v2.5")
RECALL_KS = (5, 10)
MRR_K = 10


def retrieve_by_mode(mode: str, question: str, top_k: int) -> list[dict]:
    if mode == "vector":
        return retrieve(question, top_k=top_k)
    if mode == "bm25":
        return bm25_search(question, top_k=top_k)
    if mode == "hybrid":
        return hybrid_search(question, top_k=top_k)
    if mode == "hybrid_rerank":
        return hybrid_rerank_search(question, top_k=top_k)
    raise ValueError(f"未知检索模式：{mode}")


def hit_to_row(hit: dict) -> dict:
    row = {
        "rank": hit["rank"],
        "chunk_id": hit["id"],
        "source": hit["source"],
        "score": round(hit["score"], 6),
    }
    for field in ("vector_rank", "vector_score", "bm25_rank", "bm25_score", "rrf_rank"):
        if field in hit:
            row[field] = hit[field]
    if "rerank_score" in hit:
        row["rerank_score"] = round(hit["rerank_score"], 6)
    return row


def evaluate_one(question: dict, top_k: int, mode: str) -> dict:
    start = time.perf_counter()
    hits = retrieve_by_mode(mode, question["question"], top_k)
    latency_ms = round((time.perf_counter() - start) * 1000)
    hit_ids = [hit["id"] for hit in hits]
    relevant = question["relevant_chunk_ids"]
    groups = evidence_groups_of(question)
    row = {
        "question_id": question["id"],
        "question": question["question"],
        "type": question["type"],
        "relevant_chunk_ids": relevant,
        "evidence_groups": groups,
        "latency_ms": latency_ms,
        "hits": [hit_to_row(hit) for hit in hits],
        "hit_rank": None,
        "relevant_hit_count": 0,
        "recall_at_5": None,
        "recall_at_10": None,
        "reciprocal_rank": None,
        "evidence_group_recall_at_5": evidence_group_recall(hit_ids, groups, 5),
        "complete_evidence_at_5": complete_evidence_at_k(hit_ids, groups, 5),
        "adjacent_chunk_pair_rate_at_5": round(adjacent_chunk_pair_rate(hit_ids, 5), 6),
        "distinct_sources_at_5": len({hit["source"] for hit in hits[:5]}),
        "context_chars_at_5": sum(len(hit["text"]) for hit in hits[:5]),
    }
    if relevant:
        row["hit_rank"] = hit_rank(hit_ids, relevant)
        row["relevant_hit_count"] = relevant_hit_count(hit_ids, relevant, k=MRR_K)
        row["recall_at_5"] = recall_at_k(hit_ids, relevant, k=5)
        row["recall_at_10"] = recall_at_k(hit_ids, relevant, k=10)
        row["reciprocal_rank"] = round(reciprocal_rank(hit_ids, relevant, k=MRR_K), 6)
    return row


def summarize(rows: list[dict]) -> dict:
    scored = [row for row in rows if row["recall_at_5"] is not None]
    evidence_scored = [row for row in rows if row["evidence_group_recall_at_5"] is not None]
    if not scored:
        raise ValueError("评估集中没有可计算检索指标的 chunk 标注")
    latencies = [row["latency_ms"] for row in rows]
    return {
        "scored_count": len(scored),
        "evidence_scored_count": len(evidence_scored),
        "recall_at_5": round(sum(row["recall_at_5"] for row in scored) / len(scored), 6),
        "recall_at_10": round(sum(row["recall_at_10"] for row in scored) / len(scored), 6),
        "mrr_at_10": round(sum(row["reciprocal_rank"] for row in scored) / len(scored), 6),
        "avg_relevant_coverage": round(
            sum(row["relevant_hit_count"] / len(row["relevant_chunk_ids"]) for row in scored)
            / len(scored),
            6,
        ),
        "evidence_group_recall_at_5": round(
            sum(row["evidence_group_recall_at_5"] for row in evidence_scored)
            / len(evidence_scored),
            6,
        ) if evidence_scored else None,
        "complete_evidence_at_5": round(
            sum(row["complete_evidence_at_5"] for row in evidence_scored)
            / len(evidence_scored),
            6,
        ) if evidence_scored else None,
        "avg_adjacent_chunk_pair_rate_at_5": round(
            sum(row["adjacent_chunk_pair_rate_at_5"] for row in rows) / len(rows), 6
        ),
        "avg_distinct_sources_at_5": round(
            sum(row["distinct_sources_at_5"] for row in rows) / len(rows), 3
        ),
        "avg_context_chars_at_5": round(
            sum(row["context_chars_at_5"] for row in rows) / len(rows), 1
        ),
        "latency_ms": {
            "avg": round(sum(latencies) / len(latencies), 1),
            "p50": percentile(latencies, 50),
            "p95": percentile(latencies, 95),
        },
    }


def run_metadata(mode: str, top_k: int, dataset: Path, state: dict) -> dict:
    dataset_path = dataset.resolve()
    return {
        "name": f"run-{mode}",
        "mode": mode,
        "dataset": dataset.as_posix(),
        "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
        "evidence_anchors_sha256": hashlib.sha256(EVIDENCE_ANCHORS_PATH.read_bytes()).hexdigest(),
        "top_k": top_k,
        "recall_ks": list(RECALL_KS),
        "mrr_k": MRR_K,
        "index": {key: value for key, value in state.items() if key != "runtime"},
        "retrieval": {
            "vector_candidates": VECTOR_CANDIDATES,
            "bm25_candidates": BM25_CANDIDATES,
            "rrf_k": RRF_K,
            "rerank_candidates": RERANK_CANDIDATES,
            "rerank_model": RERANK_MODEL,
            "bm25_k1": K1,
            "bm25_b": B,
        },
        "generation": {
            "model": LLM_MODEL,
            "prompt_version": PROMPT_VERSION,
            "temperature": LLM_TEMPERATURE,
            "enable_thinking": False,
        },
        "warmup": False,
        "runtime": state["runtime"],
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def render_markdown(payload: dict) -> str:
    run = payload["run"]
    summary = payload["summary"]
    rows = payload["questions"]
    lines = [
        f"# 检索评估报告：{run['name']}",
        "",
        "## 运行信息",
        "",
        f"- 模式：`{run['mode']}`",
        f"- 数据集：`{run['dataset']}`（{run['question_count']} 题）",
        f"- 索引版本：`{run['index']['index_version']}`",
        f"- chunk：{run['index']['chunk_count']}，参数 {run['index']['chunk_size']}/{run['index']['chunk_overlap']}",
        f"- Git：`{run['runtime']['git']['commit']}`，dirty={run['runtime']['git']['dirty']}",
        "",
        "## 汇总指标",
        "",
        "| 指标 | 值 |",
        "|---|---:|",
        f"| Any-hit Recall@5 | {summary['recall_at_5']:.1%} |",
        f"| Recall@10 | {summary['recall_at_10']:.1%} |",
        f"| MRR@10 | {summary['mrr_at_10']:.3f} |",
        f"| Evidence-group Recall@5 | {summary['evidence_group_recall_at_5']:.1%} |",
        f"| Complete-evidence@5 | {summary['complete_evidence_at_5']:.1%} |",
        f"| 相邻 chunk 对比例@5 | {summary['avg_adjacent_chunk_pair_rate_at_5']:.1%} |",
        f"| Top-5 平均来源数 | {summary['avg_distinct_sources_at_5']:.2f} |",
        f"| Top-5 平均上下文字符 | {summary['avg_context_chars_at_5']:.1f} |",
        f"| 延迟 P50 / P95 | {summary['latency_ms']['p50']} / {summary['latency_ms']['p95']} ms |",
        "",
        "## 未完整召回必要证据的问题",
        "",
    ]
    failed = [row for row in rows if row["complete_evidence_at_5"] == 0]
    if not failed:
        lines.append("无。")
    else:
        for row in failed:
            lines.append(
                f"- **{row['question_id']}** [{row['type']}] "
                f"evidence={row['evidence_group_recall_at_5']:.1%}：{row['question']}"
            )
    lines.extend(["", "## 逐题明细", "", "| 题 | 类型 | HitRank | R@5 | 证据组 | 完整 | 延迟ms | Top-1 |", "|---|---|---:|---:|---:|---:|---:|---|"])
    for row in rows:
        top1 = row["hits"][0]["chunk_id"] if row["hits"] else "—"
        lines.append(
            f"| {row['question_id']} | {row['type']} | {row['hit_rank'] if row['hit_rank'] is not None else '—'} | "
            f"{row['recall_at_5'] if row['recall_at_5'] is not None else '—'} | "
            f"{row['evidence_group_recall_at_5'] if row['evidence_group_recall_at_5'] is not None else '—'} | "
            f"{row['complete_evidence_at_5'] if row['complete_evidence_at_5'] is not None else '—'} | "
            f"{row['latency_ms']} | {top1} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="四模式检索评估")
    parser.add_argument("--mode", choices=("vector", "bm25", "hybrid", "hybrid_rerank"), default="vector")
    parser.add_argument("--dataset", type=Path, default=REGRESSION_PATH)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.top_k < max(RECALL_KS):
        raise SystemExit(f"--top-k 必须至少为 {max(RECALL_KS)}")

    out_path = args.out or DEFAULT_RESULTS_DIR / f"run-{args.mode}.json"
    md_path = out_path.with_suffix(".md")
    if (out_path.exists() or md_path.exists()) and not args.force:
        raise SystemExit(f"结果已存在：{out_path}（使用 --force 才允许覆盖）")

    state = verify_project_state()
    questions, _chunks = prepare_questions(
        args.dataset,
        chunk_size=state["chunk_size"],
        chunk_overlap=state["chunk_overlap"],
    )
    evaluation_start = time.perf_counter()
    rows = []
    for question in questions:
        row = evaluate_one(question, args.top_k, args.mode)
        rows.append(row)
        print(
            f"{question['id']} hit={row['hit_rank']} complete={row['complete_evidence_at_5']} "
            f"{row['latency_ms']}ms"
        )
    run = run_metadata(args.mode, args.top_k, args.dataset, state)
    run["question_count"] = len(questions)
    run["evaluation_duration_ms"] = round((time.perf_counter() - evaluation_start) * 1000)
    payload = {"run": run, "summary": summarize(rows), "questions": rows}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
