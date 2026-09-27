"""离线检索评估：跑全部评估题，输出机器可读 JSON + 人类可读 Markdown。

只评估检索，不调用 LLM（生成模型的随机性会掩盖检索问题）。

用法（项目根目录执行）：
    python -X utf8 -m evaluation.evaluate_retrieval
    python -X utf8 -m evaluation.evaluate_retrieval --mode bm25 --out data/eval/run-bm25.json
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from evaluation.metrics import (
    hit_rank,
    percentile,
    recall_at_k,
    reciprocal_rank,
    relevant_hit_count,
)
from src import vector_store
from src.config import COLLECTION_NAME, EMBEDDING_MODEL
from src.retriever import retrieve
from src.bm25_store import search as bm25_search

QUESTIONS_PATH = Path("data/eval/questions.jsonl")
DEFAULT_OUT = Path("data/eval/baseline-v1.json")

RECALL_KS = (5, 10)  # 计算哪几档 Recall（题级口径）
MRR_K = 10           # MRR 的截断深度


def load_questions() -> list[dict]:
    """读评估集：一行一题 JSONL，保持文件顺序。"""
    lines = QUESTIONS_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


def index_snapshot() -> int:
    """当前库内向量数——写进报告作为运行快照（索引变了，指标才可解释）。"""
    client = vector_store.get_client()
    collection = vector_store.get_collection(client)
    return vector_store.count(collection)

def retrieve_by_mode(mode: str, question: str, top_k: int) -> list[dict]:
    """按检索模式分发：vector = 向量链路（v1.0 生产链路）；bm25 = 关键词链路。"""
    if mode == "vector":
        return retrieve(question, top_k=top_k)
    if mode == "bm25":
        return bm25_search(question, top_k=top_k)
    raise ValueError(f"未知检索模式：{mode}")

def evaluate_one(q: dict, top_k: int, mode: str) -> dict:
    """跑一题：检索 + 计时 + 计算该题指标。"""
    start = time.perf_counter()
    hits = retrieve_by_mode(mode, q["question"], top_k)
    latency_ms = round((time.perf_counter() - start) * 1000)

    hit_ids = [h["id"] for h in hits]
    relevant = q["relevant_chunk_ids"]

    row = {
        "question_id": q["id"],
        "question": q["question"],
        "type": q["type"],
        "relevant_chunk_ids": relevant,
        "latency_ms": latency_ms,
        "hits": [
            {
                "rank": h["rank"],
                "chunk_id": h["id"],
                "source": h["source"],
                "score": round(h["score"], 4),
            }
            for h in hits
        ],
        # 以下指标只有可答题（有标注）才算；拒答题保持 None
        "hit_rank": None,
        "relevant_hit_count": 0,
        "recall_at_5": None,
        "recall_at_10": None,
        "reciprocal_rank": None,
    }
    if relevant:
        row["hit_rank"] = hit_rank(hit_ids, relevant)
        row["relevant_hit_count"] = relevant_hit_count(hit_ids, relevant, k=MRR_K)
        row["recall_at_5"] = recall_at_k(hit_ids, relevant, k=5)
        row["recall_at_10"] = recall_at_k(hit_ids, relevant, k=10)
        row["reciprocal_rank"] = round(reciprocal_rank(hit_ids, relevant, k=MRR_K), 4)
    return row


def summarize(rows: list[dict]) -> dict:
    """聚合：Recall/MRR 只统计有标注的题；延迟统计全部题（服务口径）。"""
    scored = [r for r in rows if r["recall_at_5"] is not None]
    latencies = [r["latency_ms"] for r in rows]
    n = len(scored)
    return {
        "scored_count": n,
        "recall_at_5": round(sum(r["recall_at_5"] for r in scored) / n, 4),
        "recall_at_10": round(sum(r["recall_at_10"] for r in scored) / n, 4),
        "mrr_at_10": round(sum(r["reciprocal_rank"] for r in scored) / n, 4),
        "avg_relevant_coverage": round(
            sum(r["relevant_hit_count"] / len(r["relevant_chunk_ids"]) for r in scored) / n, 4
        ),
        "latency_ms": {
            "avg": round(sum(latencies) / len(latencies), 1),
            "p50": round(percentile(latencies, 50), 1),
            "p95": round(percentile(latencies, 95), 1),
        },
    }


def render_markdown(payload: dict) -> str:
    """把整份结果渲染为人类可读报告。"""
    run = payload["run"]
    summary = payload["summary"]
    rows = payload["questions"]

    out: list[str] = []
    out.append(f"# 检索评估报告：{run['name']}")
    out.append("")
    out.append("## 运行信息")
    out.append("")
    out.append("| 项 | 值 |")
    out.append("|---|---|")
    out.append(f"| 时间 | {run['created_at']} |")
    out.append(f"| 模式 | {run['mode']} |")
    out.append(f"| top_k | {run['top_k']} |")
    out.append(f"| 集合 / 向量数 | {run['collection']} / {run['chunk_count']} |")
    out.append(f"| Embedding | {run['embedding_model']} |")
    out.append(f"| 题目数 / 参与统计 | {run['question_count']} / {summary['scored_count']}（拒答题不计入） |")
    out.append("")
    out.append("## 汇总指标")
    out.append("")
    out.append("| 指标 | 值 | 说明 |")
    out.append("|---|---:|---|")
    out.append(f"| Recall@5 | {summary['recall_at_5']:.1%} | 前 5 命中中含任一相关块的题占比 |")
    out.append(f"| Recall@10 | {summary['recall_at_10']:.1%} | 前 10 命中中含任一相关块的题占比 |")
    out.append(f"| MRR@10 | {summary['mrr_at_10']:.3f} | 首个相关块排名的倒数均值 |")
    out.append(f"| 相关块覆盖（Top-10） | {summary['avg_relevant_coverage']:.1%} | 命中相关块数 / 标注总数 |")
    out.append(
        f"| 延迟 P50 / P95 | {summary['latency_ms']['p50']} / {summary['latency_ms']['p95']} ms"
        " | 单题端到端（含查询向量化网络时间） |"
    )
    out.append("")
    out.append("## 分题型统计")
    out.append("")
    out.append("| 题型 | 题数 | Recall@5 | MRR@10 |")
    out.append("|---|---:|---:|---:|")
    by_type: dict[str, list[dict]] = {}
    for r in rows:
        if r["recall_at_5"] is None:
            continue
        by_type.setdefault(r["type"], []).append(r)
    for t in sorted(by_type):
        rs = by_type[t]
        r5 = sum(x["recall_at_5"] for x in rs) / len(rs)
        mrr = sum(x["reciprocal_rank"] for x in rs) / len(rs)
        out.append(f"| {t} | {len(rs)} | {r5:.1%} | {mrr:.3f} |")
    out.append("")
    out.append("## Recall@5 未命中的题")
    out.append("")
    failed = [r for r in rows if r["recall_at_5"] == 0]
    if not failed:
        out.append("无。")
    else:
        for r in failed:
            top5 = ", ".join(h["chunk_id"] for h in r["hits"][:5])
            out.append(f"- **{r['question_id']}** [{r['type']}] {r['question']}")
            out.append(f"  - 相关块：{', '.join(r['relevant_chunk_ids'])}")
            out.append(f"  - 实际 Top-5：{top5}")
    out.append("")
    out.append("## 逐题明细")
    out.append("")
    out.append("| 题 | 题型 | HitRank | RR@10 | R@5 | R@10 | 延迟ms | Top-1 |")
    out.append("|---|---|---:|---:|---:|---:|---:|---|")
    for r in rows:
        hr = "—" if r["hit_rank"] is None else str(r["hit_rank"])
        rr = "—" if r["reciprocal_rank"] is None else f"{r['reciprocal_rank']:.3f}"
        r5 = "—" if r["recall_at_5"] is None else str(r["recall_at_5"])
        r10 = "—" if r["recall_at_10"] is None else str(r["recall_at_10"])
        top1 = r["hits"][0]["chunk_id"] if r["hits"] else "—"
        out.append(
            f"| {r['question_id']} | {r['type']} | {hr} | {rr} | {r5} | {r10} | {r['latency_ms']} | {top1} |"
        )
    out.append("")
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="离线检索评估：跑全部评估题，产出 JSON 与 Markdown 报告")
    parser.add_argument("--mode", default="vector", help="检索模式（vector / bm25）")
    parser.add_argument("--top-k", type=int, default=10, help="每题检索候选数（默认 10，Recall@10 需要）")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help=f"JSON 结果输出路径（默认 {DEFAULT_OUT}）")
    parser.add_argument("--force", action="store_true", help="允许覆盖已存在的输出文件（默认拒绝）")
    args = parser.parse_args()

    if args.mode not in ("vector", "bm25"):
        raise SystemExit(f"未知检索模式：{args.mode}（当前支持 vector / bm25）")
    if args.top_k < max(RECALL_KS):
        raise SystemExit(f"--top-k={args.top_k} 小于评估深度 {max(RECALL_KS)}，Recall@10 会失真")

    out_path = Path(args.out)
    md_path = out_path.with_suffix(".md")
    if out_path.exists() and not args.force:
        raise SystemExit(f"{out_path} 已存在：基线结果不允许被覆盖。要重跑请先删除文件，或显式加 --force")

    questions = load_questions()
    chunk_count = index_snapshot()
    print(f"检索评估开始：{len(questions)} 题，模式={args.mode}，top_k={args.top_k}，索引 {chunk_count} 条")
    print("-" * 72)

    rows: list[dict] = []
    for q in questions:
        row = evaluate_one(q, top_k=args.top_k, mode=args.mode)
        rows.append(row)
        mark = {None: "-", 0: "X", 1: "O"}[row["recall_at_5"]]
        print(f"  {mark} {row['question_id']} [{row['type']}] hit_rank={row['hit_rank']} {row['latency_ms']}ms")

    summary = summarize(rows)
    payload = {
        "run": {
            "name": out_path.stem,
            "mode": args.mode,
            "top_k": args.top_k,
            "recall_ks": list(RECALL_KS),
            "mrr_k": MRR_K,
            "collection": COLLECTION_NAME,
            "chunk_count": chunk_count,
            "embedding_model": EMBEDDING_MODEL,
            "question_count": len(questions),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
        "summary": summary,
        "questions": rows,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")

    print("-" * 72)
    print(
        f"Recall@5 = {summary['recall_at_5']:.1%} | "
        f"Recall@10 = {summary['recall_at_10']:.1%} | "
        f"MRR@10 = {summary['mrr_at_10']:.3f}"
    )
    print(
        f"延迟：avg={summary['latency_ms']['avg']}ms | "
        f"P50={summary['latency_ms']['p50']}ms | P95={summary['latency_ms']['p95']}ms"
    )
    print(f"已写入：{out_path}（机器可读）与 {md_path}（人类可读）")


if __name__ == "__main__":
    main()