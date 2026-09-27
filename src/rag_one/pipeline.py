"""四链路「带阶段追踪」统一入口：检索 → 生成，返回中间态与耗时（供界面 / 调试）。

与 rag_one.rag.ask 的区别：ask 只跑向量链路、只返回最终结果；
本模块跑四条链路（vector / bm25 / hybrid / hybrid_rerank），并把
「候选池 + 各阶段名次 + 分阶段耗时」保留下来——界面据此展示全过程。

组装说明：hybrid / hybrid_rerank 为了按阶段分开计时、并保留候选全表，
在此按组合层（hybrid_retriever / hybrid_reranker）同一逻辑展开组装——
同函数、同参数、同截断口径（截头部即 rank 1..K，无需重编号）：
- 混合：两路候选 → rrf_fuse（取 candidate_k 条留全表，前 top_k 进 Prompt）；
- 混合重排：融合候选 → rerank（top_k=候选数，一次拿回全部重排分）→ 前 top_k。
"""

import time

from rag_one.generation.generator import generate_answer
from rag_one.indexing.bm25_store import search as bm25_search
from rag_one.retrieval.fusion import RRF_K, rrf_fuse
from rag_one.retrieval.hybrid import BM25_CANDIDATES, VECTOR_CANDIDATES
from rag_one.retrieval.hybrid_reranker import RERANK_CANDIDATES
from rag_one.retrieval.reranker import RerankError, last_usage, rerank
from rag_one.retrieval.vector import DEFAULT_TOP_K, retrieve

MODES = ("vector", "bm25", "hybrid", "hybrid_rerank")


def _ms(start: float, end: float) -> int:
    """秒差转毫秒（整数，与评估脚本同口径）。"""
    return round((end - start) * 1000)


def run_chain(
    mode: str,
    question: str,
    top_k: int = DEFAULT_TOP_K,
    vector_k: int = VECTOR_CANDIDATES,
    bm25_k: int = BM25_CANDIDATES,
    rrf_k: int = RRF_K,
    candidate_k: int = RERANK_CANDIDATES,
    fallback: bool = True,
) -> dict:
    """跑一条链路：检索（按模式）→ 生成；返回候选池、最终 hits、分阶段耗时与 token。

    - stages：按执行顺序记录每段 {"name", "elapsed_ms", "count"}；
    - candidates：候选池全表（各链路字段自然不同，统一补 final_rank）；
    - warnings：回退等异常说明（不吞错：严格模式失败照抛）。
    """
    if mode not in MODES:
        raise ValueError(f"未知检索模式：{mode}（可选：{' / '.join(MODES)}）")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question 不能为空")
    if top_k < 1:
        raise ValueError(f"top_k 必须 >= 1，收到 {top_k}")

    stages: list[dict] = []
    warnings: list[str] = []
    rerank_tokens: int | None = None
    total_start = time.perf_counter()

    if mode == "vector":
        start = time.perf_counter()
        hits = retrieve(question, top_k=top_k)
        stages.append({"name": "向量召回", "elapsed_ms": _ms(start, time.perf_counter()), "count": len(hits)})
        candidates = hits

    elif mode == "bm25":
        start = time.perf_counter()
        hits = bm25_search(question, top_k=top_k)
        stages.append({"name": "BM25 召回", "elapsed_ms": _ms(start, time.perf_counter()), "count": len(hits)})
        candidates = hits

    elif mode == "hybrid":
        start = time.perf_counter()
        vector_hits = retrieve(question, top_k=vector_k)
        stages.append({"name": "向量召回", "elapsed_ms": _ms(start, time.perf_counter()), "count": len(vector_hits)})
        start = time.perf_counter()
        bm25_hits = bm25_search(question, top_k=bm25_k)
        stages.append({"name": "BM25 召回", "elapsed_ms": _ms(start, time.perf_counter()), "count": len(bm25_hits)})
        start = time.perf_counter()
        fused = rrf_fuse({"vector": vector_hits, "bm25": bm25_hits}, top_k=candidate_k, k=rrf_k)
        stages.append({"name": "RRF 融合", "elapsed_ms": _ms(start, time.perf_counter()), "count": len(fused)})
        candidates = fused
        hits = fused[:top_k]

    else:  # hybrid_rerank
        start = time.perf_counter()
        vector_hits = retrieve(question, top_k=vector_k)
        stages.append({"name": "向量召回", "elapsed_ms": _ms(start, time.perf_counter()), "count": len(vector_hits)})
        start = time.perf_counter()
        bm25_hits = bm25_search(question, top_k=bm25_k)
        stages.append({"name": "BM25 召回", "elapsed_ms": _ms(start, time.perf_counter()), "count": len(bm25_hits)})
        start = time.perf_counter()
        fused = rrf_fuse({"vector": vector_hits, "bm25": bm25_hits}, top_k=candidate_k, k=rrf_k)
        stages.append({"name": "RRF 融合", "elapsed_ms": _ms(start, time.perf_counter()), "count": len(fused)})

        for hit in fused:
            hit["rrf_rank"] = hit["rank"]  # 重排前名次留档（rerank 会重写 rank）

        start = time.perf_counter()
        try:
            # top_k=len(fused)：一次拿回全部候选的重排分，排序后本地截断
            ranked = rerank(question, fused, top_k=len(fused))
            rerank_tokens = last_usage().get("tokens", {}).get("input_tokens")
            candidates = ranked
            hits = ranked[:top_k]
        except RerankError as exc:
            if not fallback:
                raise
            warnings.append(f"Reranker 调用失败，已回退融合结果：{exc}")
            candidates = fused
            hits = fused[:top_k]
        stages.append({"name": "Reranker 精排", "elapsed_ms": _ms(start, time.perf_counter()), "count": len(fused)})

    start = time.perf_counter()
    result = generate_answer(question, hits)
    stages.append({"name": "答案生成", "elapsed_ms": _ms(start, time.perf_counter()), "count": None})
    total_ms = _ms(total_start, time.perf_counter())

    # 候选池统一补 final_rank：进最终 Top-K 的记录名次，未进的为 None
    final_rank_of = {h["id"]: i for i, h in enumerate(hits, start=1)}
    for item in candidates:
        item["final_rank"] = final_rank_of.get(item["id"])

    return {
        "question": question,
        "mode": mode,
        "settings": {
            "top_k": top_k,
            "vector_k": vector_k,
            "bm25_k": bm25_k,
            "rrf_k": rrf_k,
            "candidate_k": candidate_k,
        },
        "stages": stages,
        "total_ms": total_ms,
        "candidates": candidates,
        "hits": hits,
        "answer": result["answer"],
        "usage": result["usage"],
        "prompt_version": result.get("prompt_version"),
        "citation_validation": result.get("citation_validation"),
        "rerank_tokens": rerank_tokens,
        "warnings": warnings,
    }
