"""混合检索 + 重排：把 RRF 融合候选交给 Reranker 精排，输出最终 Top-K。

链路：问题 → 混合召回（向量 + BM25 → RRF，Top-20）→ Reranker 逐对打分 → Top-K（给 LLM）

为什么分两段：召回阶段「宁可多召回、别漏」，重排阶段「把最相关的排到最前」——
交叉编码重排准但慢，只适合小候选集，所以宽进（20）窄出（Top-K）。
"""

from src.hybrid_retriever import hybrid_search
from src.reranker import RerankError, rerank

RERANK_CANDIDATES = 20  # 送进重排的融合候选数（v2.0 规划起点值）
RERANK_TOP_K = 5        # 重排后最终条数（产品口径：进 Prompt 的上下文条数）


def hybrid_rerank_search(
    question: str,
    top_k: int = RERANK_TOP_K,
    candidate_k: int = RERANK_CANDIDATES,
    fallback: bool = True,
) -> list[dict]:
    """混合召回 + 重排：返回精排后的 top_k 个 chunk。

    - 先取 candidate_k 条融合候选，逐条记下重排前名次（rrf_rank）；
    - 再交给 rerank 精排，rank 被重写为最终名次；
    - fallback=True：Rerank API 失败时回退返回融合 Top-K（无 rerank_score，其余字段齐全）
      并打印警告——宁可少一层精排，也不能让整条检索链断掉；
    - fallback=False：失败直接抛 RerankError（严格模式，不返回半截结果）。
    """
    fused = hybrid_search(question, top_k=candidate_k)
    for hit in fused:
        hit["rrf_rank"] = hit["rank"]  # 重排前名次先留档（rerank 会重写 rank）

    try:
        return rerank(question, fused, top_k=top_k)
    except RerankError as exc:
        if not fallback:
            raise
        print(f"[WARN] Reranker 调用失败，回退到 hybrid 融合结果：{exc}")
        return fused[:top_k]


def format_reranked(question: str, hits: list[dict]) -> str:
    """重排结果终端排版：最终名次 + 重排分 + 三级排名（rrf / vector / bm25）。"""
    if not hits:
        return f"问题：{question}\n（未检索到任何结果）"

    lines = [f"问题：{question}", ""]
    for hit in hits:
        v = hit["vector_rank"] if hit["vector_rank"] is not None else "—"
        b = hit["bm25_rank"] if hit["bm25_rank"] is not None else "—"
        score = f'{hit["rerank_score"]:.4f}' if "rerank_score" in hit else "—（回退）"
        lines.append(
            f'Final Rank {hit["rank"]} | rerank={score} | rrf={hit["rrf_rank"]}'
            f' vector={v} bm25={b} | {hit["source"]}'
        )
        lines.append(f'  chunk: {hit["id"]}')
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    # 同款三条 demo（与 hybrid_retriever 一致）：q01 两路都强；q20 向量弱；q32 BM25 弱
    demo_questions = [
        "普通员工去上海出差，酒店每晚含税最高可以报销多少？",
        "外出拜访客户会占用每周远程办公天数吗？",
        "台风导致地铁停运，今天能临时申请在家办公吗？",
    ]
    for question in demo_questions:
        print(format_reranked(question, hybrid_rerank_search(question)))
        print("=" * 60)
