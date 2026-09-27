"""vector / hybrid_rerank 的端到端答案与引用原始产物评估。"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from evaluation.dataset import (
    REGRESSION_PATH,
    evidence_groups_of,
    prepare_questions,
)
from evaluation.evaluate_retrieval import hit_to_row, run_metadata
from evaluation.metrics import (
    complete_evidence_at_k,
    evidence_group_recall,
    hit_rank,
    percentile,
    recall_at_k,
)
from rag_one.generation.generator import generate_answer
from rag_one.retrieval.hybrid import hybrid_search
from rag_one.retrieval.hybrid_reranker import RERANK_CANDIDATES
from rag_one.retrieval.reranker import RerankError, last_usage, rerank
from rag_one.retrieval.vector import retrieve
from rag_one.state import verify_project_state

E2E_MODES = ("vector", "hybrid_rerank")
E2E_TOP_K = 5
CITATION_RE = re.compile(r"\[(\d+)\]")
DEFAULT_RESULTS_DIR = Path("data/eval/results/v2.5")


def _ms(start: float, end: float) -> int:
    return round((end - start) * 1000)


def citations_of(answer: str) -> list[int]:
    seen: list[int] = []
    for match in CITATION_RE.finditer(answer):
        number = int(match.group(1))
        if number not in seen:
            seen.append(number)
    return seen


def retrieve_e2e(mode: str, question: str) -> tuple[list[dict], dict, dict | None]:
    if mode == "vector":
        start = time.perf_counter()
        hits = retrieve(question, top_k=E2E_TOP_K)
        return hits, {"retrieve": _ms(start, time.perf_counter())}, None

    start = time.perf_counter()
    fused = hybrid_search(question, top_k=RERANK_CANDIDATES)
    split = time.perf_counter()
    for hit in fused:
        hit["rrf_rank"] = hit["rank"]
    meta = {"fallback": False, "input_tokens": None}
    try:
        hits = rerank(question, fused, top_k=E2E_TOP_K)
        meta["input_tokens"] = last_usage().get("tokens", {}).get("input_tokens")
    except RerankError as exc:
        print(f"[WARN] Reranker 失败，回退 hybrid：{exc}")
        meta["fallback"] = True
        hits = fused[:E2E_TOP_K]
    end = time.perf_counter()
    return hits, {"fuse": _ms(start, split), "rerank": _ms(split, end)}, meta


def evaluate_one(question: dict, mode: str) -> dict:
    start = time.perf_counter()
    hits, latency, rerank_meta = retrieve_e2e(mode, question["question"])
    split = time.perf_counter()
    generated = generate_answer(question["question"], hits)
    end = time.perf_counter()
    latency["generate"] = _ms(split, end)
    latency["total"] = _ms(start, end)
    hit_ids = [hit["id"] for hit in hits]
    relevant = question["relevant_chunk_ids"]
    groups = evidence_groups_of(question)
    row = {
        "question_id": question["id"],
        "question": question["question"],
        "type": question["type"],
        "expected_answer": question["expected_answer"],
        "relevant_chunk_ids": relevant,
        "evidence_groups": groups,
        "hits": [hit_to_row(hit) for hit in hits],
        "hit_rank": hit_rank(hit_ids, relevant) if relevant else None,
        "recall_at_5": recall_at_k(hit_ids, relevant, E2E_TOP_K) if relevant else None,
        "evidence_group_recall_at_5": evidence_group_recall(hit_ids, groups, E2E_TOP_K),
        "complete_evidence_at_5": complete_evidence_at_k(hit_ids, groups, E2E_TOP_K),
        "answer": generated["answer"],
        "citations": citations_of(generated["answer"]),
        "citation_validation": generated["citation_validation"],
        "usage": generated["usage"],
        "prompt_version": generated["prompt_version"],
        "latency_ms": latency,
    }
    if rerank_meta is not None:
        row["rerank_fallback"] = rerank_meta["fallback"]
        row["rerank_input_tokens"] = rerank_meta["input_tokens"]
    return row


def _stats(values: list[float]) -> dict:
    return {
        "avg": round(sum(values) / len(values), 1),
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
    }


def summarize(rows: list[dict], mode: str) -> dict:
    if not rows:
        raise ValueError("评估结果不能为空")
    scored = [row for row in rows if row["recall_at_5"] is not None]
    evidence = [row for row in rows if row["complete_evidence_at_5"] is not None]
    if not scored:
        raise ValueError("评估集中没有可计算检索指标的 chunk 标注")
    if not evidence:
        raise ValueError("评估集中没有可计算必要证据的 evidence_groups")
    summary = {
        "scored_count": len(scored),
        "recall_at_5": round(sum(row["recall_at_5"] for row in scored) / len(scored), 6),
        "evidence_group_recall_at_5": round(
            sum(row["evidence_group_recall_at_5"] for row in evidence) / len(evidence), 6
        ),
        "complete_evidence_at_5": round(
            sum(row["complete_evidence_at_5"] for row in evidence) / len(evidence), 6
        ),
        "prompt_tokens": _stats([row["usage"]["prompt_tokens"] for row in rows]),
        "completion_tokens": _stats([row["usage"]["completion_tokens"] for row in rows]),
        "invalid_citation_answers": sum(bool(row["citation_validation"]["invalid_citations"]) for row in rows),
        "refusal_with_citations": sum(row["citation_validation"]["refusal_has_citations"] for row in rows),
        "latency_ms": {},
    }
    for key in ("retrieve", "fuse", "rerank", "generate", "total"):
        values = [row["latency_ms"][key] for row in rows if key in row["latency_ms"]]
        if values:
            summary["latency_ms"][key] = _stats(values)
    if mode == "hybrid_rerank":
        tokens = [row["rerank_input_tokens"] for row in rows if row.get("rerank_input_tokens") is not None]
        summary["rerank_input_tokens"] = _stats(tokens) if tokens else None
        summary["fallback_count"] = sum(bool(row.get("rerank_fallback")) for row in rows)
    return summary


def render_markdown(payload: dict) -> str:
    run = payload["run"]
    summary = payload["summary"]
    lines = [
        f"# 端到端评估原始报告：{run['name']}",
        "",
        "> 答案正确率、严格引用支持性和幻觉仍需人工判定；本报告不冒充自动质量结论。",
        "",
        f"- 数据集：`{run['dataset']}`（{run['question_count']} 题）",
        f"- 模式：`{run['mode']}`",
        f"- 索引：`{run['index']['index_version']}`",
        f"- Prompt：`{run['generation']['prompt_version']}`",
        "",
        "## 自动指标",
        "",
        "| 指标 | 值 |",
        "|---|---:|",
        f"| Any-hit Recall@5 | {summary['recall_at_5']:.1%} |",
        f"| Evidence-group Recall@5 | {summary['evidence_group_recall_at_5']:.1%} |",
        f"| Complete-evidence@5 | {summary['complete_evidence_at_5']:.1%} |",
        f"| 非法引用编号答案数 | {summary['invalid_citation_answers']} |",
        f"| 拒答但仍附编号答案数 | {summary['refusal_with_citations']} |",
        "",
        "## 逐题答案",
        "",
    ]
    for row in payload["questions"]:
        lines.extend(
            [
                f"### {row['question_id']} [{row['type']}]",
                "",
                f"- 问题：{row['question']}",
                f"- 期望：{row['expected_answer']}",
                f"- HitRank：{row['hit_rank'] if row['hit_rank'] is not None else '—'}",
                f"- 必要证据完整：{row['complete_evidence_at_5'] if row['complete_evidence_at_5'] is not None else '—'}",
                f"- 引用编号：{row['citations']}",
                "",
                row["answer"],
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="端到端答案与引用评估")
    parser.add_argument("--mode", choices=E2E_MODES, required=True)
    parser.add_argument("--dataset", type=Path, default=REGRESSION_PATH)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit 必须 >= 1")
    suffix = args.dataset.stem
    out_path = args.out or DEFAULT_RESULTS_DIR / f"run-e2e-{args.mode}-{suffix}.json"
    md_path = out_path.with_suffix(".md")
    if (out_path.exists() or md_path.exists()) and not args.force:
        raise SystemExit(f"结果已存在：{out_path}（使用 --force 才允许覆盖）")

    state = verify_project_state()
    questions, _chunks = prepare_questions(
        args.dataset,
        chunk_size=state["chunk_size"],
        chunk_overlap=state["chunk_overlap"],
    )
    if args.limit is not None:
        questions = questions[: args.limit]
    rows = []
    evaluation_start = time.perf_counter()
    for question in questions:
        row = evaluate_one(question, args.mode)
        rows.append(row)
        print(
            f"{question['id']} hit={row['hit_rank']} complete={row['complete_evidence_at_5']} "
            f"citations={row['citations']} total={row['latency_ms']['total']}ms"
        )
    run = run_metadata(args.mode, E2E_TOP_K, args.dataset, state)
    run["name"] = out_path.stem
    run["question_count"] = len(questions)
    run["limit"] = args.limit
    run["evaluation_duration_ms"] = round((time.perf_counter() - evaluation_start) * 1000)
    payload = {"run": run, "summary": summarize(rows, args.mode), "questions": rows}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
