"""离线端到端评估：检索 → 生成（LLM 照资料答题），输出机器可读 JSON + 人类可读 Markdown。

v2.0 阶段六：对两条稳定链路做端到端答案评估——
- E1 = vector（向量 Top-5）；
- E4 = hybrid_rerank（混合召回 Top-20 → Reranker 精排 → Top-5）。

记录：Top-5 命中与 chunk 级指标、生成答案与 token 用量、各阶段延迟
（E1：检索 + 生成；E4：召回融合 + 重排 + 生成）。

说明：
- E4 链路在脚本内按 src.hybrid_reranker 组合层同一逻辑组装，为了把召回融合 / 重排
  两段延迟分开记账（交付链路仍是 hybrid_rerank_search）；
- 回答质量（答案正确 / 引用正确 / 幻觉）属人工走查口径，本脚本只记录原始答案与证据，
  判定结果填写进 data/eval/eval-report.md。

用法（项目根目录执行）：
    python -X utf8 -m evaluation.evaluate_e2e --mode vector
    python -X utf8 -m evaluation.evaluate_e2e --mode hybrid_rerank
    python -X utf8 -m evaluation.evaluate_e2e --mode vector --out data/eval/run-e2e-vector.json
"""

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

from evaluation.evaluate_retrieval import hit_to_row, index_snapshot, load_questions
from evaluation.metrics import hit_rank, percentile, recall_at_k, relevant_hit_count
from src.config import COLLECTION_NAME, EMBEDDING_MODEL, LLM_MODEL
from src.generator import generate_answer
from src.hybrid_reranker import RERANK_CANDIDATES
from src.hybrid_retriever import hybrid_search
from src.reranker import RerankError, last_usage, rerank
from src.retriever import retrieve

E2E_MODES = ("vector", "hybrid_rerank")
E2E_TOP_K = 5  # 进 Prompt 的最终条数（产品口径）
LATENCY_KEYS = ("retrieve", "fuse", "rerank", "generate", "total")
CITATION_RE = re.compile(r"\[(\d+)\]")


def to_ms(start: float, end: float) -> int:
    """秒差转毫秒（整数，与检索评估同口径）。"""
    return round((end - start) * 1000)


def citations_of(answer: str) -> list[int]:
    """抽取答案里的引用编号 [n]，按首次出现顺序去重。"""
    seen: list[int] = []
    for match in CITATION_RE.finditer(answer):
        n = int(match.group(1))
        if n not in seen:
            seen.append(n)
    return seen


def retrieve_e2e(mode: str, question: str, top_k: int = E2E_TOP_K) -> tuple[list[dict], dict, dict | None]:
    """执行检索并分段计时；返回 (hits, latency, rerank_meta)。

    rerank_meta 仅 E4 有值：{"fallback": bool, "input_tokens": int | None}。
    """
    if mode == "vector":
        start = time.perf_counter()
        hits = retrieve(question, top_k=top_k)
        return hits, {"retrieve": to_ms(start, time.perf_counter())}, None

    # hybrid_rerank：召回融合 / 重排分开计时（与 src.hybrid_reranker 组合层同一逻辑）
    start = time.perf_counter()
    fused = hybrid_search(question, top_k=RERANK_CANDIDATES)
    split = time.perf_counter()
    for hit in fused:
        hit["rrf_rank"] = hit["rank"]  # 重排前名次先留档（rerank 会重写 rank）
    meta = {"fallback": False, "input_tokens": None}
    try:
        hits = rerank(question, fused, top_k=top_k)
        meta["input_tokens"] = last_usage().get("tokens", {}).get("input_tokens")
    except RerankError as exc:
        print(f"[WARN] Reranker 调用失败，回退到 hybrid 融合结果：{exc}")
        meta["fallback"] = True
        hits = fused[:top_k]
    end = time.perf_counter()
    return hits, {"fuse": to_ms(start, split), "rerank": to_ms(split, end)}, meta


def evaluate_one(q: dict, mode: str) -> dict:
    """跑一题端到端：检索 → 生成，返回一条机器可读记录。"""
    start = time.perf_counter()
    hits, latency, rerank_meta = retrieve_e2e(mode, q["question"])
    split = time.perf_counter()
    result = generate_answer(q["question"], hits)
    end = time.perf_counter()
    latency["generate"] = to_ms(split, end)
    latency["total"] = to_ms(start, end)

    hit_ids = [h["id"] for h in hits]
    relevant = q["relevant_chunk_ids"]

    row = {
        "question_id": q["id"],
        "question": q["question"],
        "type": q["type"],
        "expected_answer": q["expected_answer"],
        "relevant_chunk_ids": relevant,
        "hits": [hit_to_row(h) for h in hits],
        # 以下指标只有可答题（有标注）才算；拒答题保持 None
        "hit_rank": None,
        "relevant_hit_count": 0,
        "recall_at_5": None,
        "answer": result["answer"],
        "usage": result["usage"],
        "latency_ms": latency,
    }
    if relevant:
        row["hit_rank"] = hit_rank(hit_ids, relevant)
        row["relevant_hit_count"] = relevant_hit_count(hit_ids, relevant, k=E2E_TOP_K)
        row["recall_at_5"] = recall_at_k(hit_ids, relevant, k=E2E_TOP_K)
    if rerank_meta is not None:
        row["rerank_fallback"] = rerank_meta["fallback"]
        row["rerank_input_tokens"] = rerank_meta["input_tokens"]
    return row


def stats(values: list) -> dict:
    """avg / p50 / p95 三件套。"""
    return {
        "avg": round(sum(values) / len(values), 1),
        "p50": round(percentile(values, 50), 1),
        "p95": round(percentile(values, 95), 1),
    }


def summarize(rows: list[dict], mode: str) -> dict:
    """聚合汇总：Recall 只统计有标注的题；延迟与 token 统计全部题（服务口径）。"""
    scored = [r for r in rows if r["recall_at_5"] is not None]
    n = len(scored)
    summary = {
        "scored_count": n,
        "recall_at_5": round(sum(r["recall_at_5"] for r in scored) / n, 4),
        "avg_relevant_coverage": round(
            sum(r["relevant_hit_count"] / len(r["relevant_chunk_ids"]) for r in scored) / n, 4
        ),
        "prompt_tokens": stats([r["usage"]["prompt_tokens"] for r in rows]),
        "completion_tokens": stats([r["usage"]["completion_tokens"] for r in rows]),
        "latency_ms": {},
    }
    for key in LATENCY_KEYS:
        values = [r["latency_ms"][key] for r in rows if key in r["latency_ms"]]
        if values:
            summary["latency_ms"][key] = stats(values)
    if mode == "hybrid_rerank":
        tokens = [r["rerank_input_tokens"] for r in rows if r["rerank_input_tokens"] is not None]
        summary["rerank_input_tokens"] = stats(tokens) if tokens else None
        summary["fallback_count"] = sum(1 for r in rows if r["rerank_fallback"])
    return summary


def render_markdown(payload: dict) -> str:
    """把整份结果渲染为人类可读报告。"""
    run = payload["run"]
    summary = payload["summary"]
    rows = payload["questions"]
    lat = summary["latency_ms"]

    out: list[str] = []
    out.append(f"# 端到端评估报告：{run['name']}")
    out.append("")
    out.append("## 运行信息")
    out.append("")
    out.append("| 项 | 值 |")
    out.append("|---|---|")
    out.append(f"| 时间 | {run['created_at']} |")
    out.append(f"| 模式 | {run['mode']} |")
    out.append(f"| 最终 Top-K | {run['top_k']} |")
    out.append(f"| 题目数 / 参与统计 | {run['question_count']} / {summary['scored_count']}（拒答题不计入） |")
    out.append(f"| 集合 / 向量数 | {run['collection']} / {run['chunk_count']} |")
    out.append(f"| Embedding / LLM | {run['embedding_model']} / {run['llm_model']} |")
    out.append("")
    out.append("## 汇总指标")
    out.append("")
    out.append("| 指标 | 值 | 说明 |")
    out.append("|---|---:|---|")
    out.append(f"| Recall@5（chunk 级） | {summary['recall_at_5']:.1%} | 前 5 命中含任一相关块的题占比 |")
    out.append(f"| 相关块覆盖（Top-5） | {summary['avg_relevant_coverage']:.1%} | 命中相关块数 / 标注总数 |")
    pt = summary["prompt_tokens"]
    ct = summary["completion_tokens"]
    out.append(
        f"| Prompt tokens | avg {pt['avg']:.0f} / P50 {pt['p50']:.0f} / P95 {pt['p95']:.0f}"
        " | 生成请求输入 token（含 Top-5 上下文） |"
    )
    out.append(
        f"| Completion tokens | avg {ct['avg']:.0f} / P50 {ct['p50']:.0f} / P95 {ct['p95']:.0f}"
        " | 生成输出 token |"
    )
    for key, label, note in (
        ("retrieve", "检索延迟", "查询向量化 + 向量库 Top-K（E1）"),
        ("fuse", "召回融合延迟", "双路召回 + RRF 融合（E4）"),
        ("rerank", "重排延迟", "Rerank API 逐对打分（E4）"),
        ("generate", "生成延迟", "LLM 答题"),
        ("total", "总延迟", "单题端到端"),
    ):
        if key in lat:
            out.append(f"| {label} | P50 {lat[key]['p50']:.0f} / P95 {lat[key]['p95']:.0f} ms | {note} |")
    if summary.get("rerank_input_tokens"):
        rt = summary["rerank_input_tokens"]
        out.append(
            f"| 重排输入 tokens | avg {rt['avg']:.0f} / P50 {rt['p50']:.0f}"
            " | Rerank API 计费口径（E4） |"
        )
        out.append(f"| 重排回退次数 | {summary['fallback_count']} | 失败回退 hybrid 的题数（应为 0） |")
    out.append("")
    out.append("## 逐题明细")
    out.append("")
    out.append("| 题 | 题型 | HitRank | 检索ms | 融合ms | 重排ms | 生成ms | 总ms | prompt_tok | completion_tok |")
    out.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        hr = "—" if r["hit_rank"] is None else str(r["hit_rank"])
        lm = r["latency_ms"]
        cells = [
            r["question_id"],
            r["type"],
            hr,
            str(lm.get("retrieve", "—")),
            str(lm.get("fuse", "—")),
            str(lm.get("rerank", "—")),
            str(lm["generate"]),
            str(lm["total"]),
            str(r["usage"]["prompt_tokens"]),
            str(r["usage"]["completion_tokens"]),
        ]
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    out.append("## 逐题答案与引用")
    out.append("")
    for r in rows:
        hr = "—" if r["hit_rank"] is None else str(r["hit_rank"])
        out.append(f"### {r['question_id']} [{r['type']}] HitRank={hr}")
        out.append("")
        if r.get("rerank_fallback"):
            out.append("> 注意：本题重排失败，已回退融合结果（无 rerank_score）。")
            out.append("")
        out.append(f"**问题**：{r['question']}")
        out.append("")
        out.append(f"**期望答案**：{r['expected_answer']}")
        out.append("")
        out.append(f"**答案**：{r['answer']}")
        out.append("")
        cite = citations_of(r["answer"])
        out.append(f"**引用编号**：{'、'.join(f'[{n}]' for n in cite) if cite else '（无）'}")
        out.append("")
        rel = set(r["relevant_chunk_ids"])
        marks = []
        for h in r["hits"]:
            ok = "✓" if h["chunk_id"] in rel else "✗"
            marks.append(f"{h['rank']}.{ok} {h['chunk_id']}")
        out.append(f"**命中**：{' | '.join(marks)}")
        out.append("")
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="端到端评估：检索 → 生成，产出 JSON 与 Markdown 报告")
    parser.add_argument("--mode", required=True, choices=E2E_MODES, help="链路：vector（E1）/ hybrid_rerank（E4）")
    parser.add_argument("--out", default=None, help="JSON 输出路径（默认 data/eval/run-e2e-<mode>.json）")
    parser.add_argument("--limit", type=int, default=None, help="只跑前 N 题（调试用；正式评估不要带）")
    parser.add_argument("--force", action="store_true", help="允许覆盖已存在的输出文件（默认拒绝）")
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else Path(f"data/eval/run-e2e-{args.mode}.json")
    md_path = out_path.with_suffix(".md")
    if out_path.exists() and not args.force:
        raise SystemExit(f"{out_path} 已存在：评估产物不允许被覆盖。要重跑请先删除文件，或显式加 --force")

    questions = load_questions()
    if args.limit:
        questions = questions[: args.limit]
    chunk_count = index_snapshot()
    print(f"端到端评估开始：{len(questions)} 题，模式={args.mode}，Top-K={E2E_TOP_K}，索引 {chunk_count} 条")
    print("-" * 72)

    rows: list[dict] = []
    for q in questions:
        row = evaluate_one(q, args.mode)
        rows.append(row)
        mark = {None: "-", 0: "X", 1: "O"}[row["recall_at_5"]]
        print(
            f"  {mark} {row['question_id']} [{row['type']}] hit_rank={row['hit_rank']} "
            f"总延迟={row['latency_ms']['total']}ms prompt={row['usage']['prompt_tokens']}"
        )

    summary = summarize(rows, args.mode)
    payload = {
        "run": {
            "name": out_path.stem,
            "mode": args.mode,
            "top_k": E2E_TOP_K,
            "collection": COLLECTION_NAME,
            "chunk_count": chunk_count,
            "embedding_model": EMBEDDING_MODEL,
            "llm_model": LLM_MODEL,
            "question_count": len(questions),
            "limit": args.limit,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
        "summary": summary,
        "questions": rows,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")

    print("-" * 72)
    lat = summary["latency_ms"]
    print(f"Recall@5（chunk 级）= {summary['recall_at_5']:.1%}")
    print(f"总延迟：avg={lat['total']['avg']}ms | P50={lat['total']['p50']}ms | P95={lat['total']['p95']}ms")
    print(f"Prompt tokens：avg={summary['prompt_tokens']['avg']} | P50={summary['prompt_tokens']['p50']}")
    print(f"已写入：{out_path}（机器可读）与 {md_path}（人类可读）")


if __name__ == "__main__":
    main()
