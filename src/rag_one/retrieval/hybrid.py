"""混合检索：向量 + BM25 双路召回，RRF 融合成一个统一排名。

链路：问题 ─┬→ 向量 Top-N（retriever.retrieve）
            └→ BM25  Top-N（bm25_store.search） → rrf_fuse → 融合 Top-K

两路候选数（默认 20）刻意大于最终输出（top_k）：给融合留空间——
单路排第 15、另一路排第 1 的 chunk，能在融合后进入最终前 10。
"""

from rag_one.indexing.bm25_store import search as bm25_search
from rag_one.retrieval.fusion import RRF_K, rrf_fuse
from rag_one.retrieval.vector import retrieve

VECTOR_CANDIDATES = 20  # 向量路候选数（v2.0 规划起点值，后续可做单变量实验）
BM25_CANDIDATES = 20    # BM25 路候选数（同上）


def hybrid_search(
    question: str,
    top_k: int = 10,
    vector_k: int = VECTOR_CANDIDATES,
    bm25_k: int = BM25_CANDIDATES,
    rrf_k: int = RRF_K,
) -> list[dict]:
    """双路召回 + RRF 融合：返回统一排名的 top_k 个 chunk（字段见 rrf_fuse）。"""
    vector_hits = retrieve(question, top_k=vector_k)
    bm25_hits = bm25_search(question, top_k=bm25_k)
    return rrf_fuse({"vector": vector_hits, "bm25": bm25_hits}, top_k=top_k, k=rrf_k)


def format_fused(question: str, hits: list[dict]) -> str:
    """融合结果的终端排版：融合名次/分数 + 两路原始排名（未命中显示 —）。"""
    if not hits:
        return f"问题：{question}\n（未检索到任何结果）"

    lines = [f"问题：{question}", ""]
    for hit in hits:
        v = hit["vector_rank"] if hit["vector_rank"] is not None else "—"
        b = hit["bm25_rank"] if hit["bm25_rank"] is not None else "—"
        lines.append(
            f'RRF Rank {hit["rank"]} | rrf={hit["score"]:.4f} | vector={v} bm25={b} | {hit["source"]}'
        )
        lines.append(f'  chunk: {hit["id"]}')
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    # 三条 demo 与评估集同题，覆盖三种典型情况：
    # q01 两路都强；q20 向量弱（基线 rank 7）；q32 BM25 弱（rank 5）
    demo_questions = [
        "普通员工去上海出差，酒店每晚含税最高可以报销多少？",
        "外出拜访客户会占用每周远程办公天数吗？",
        "台风导致地铁停运，今天能临时申请在家办公吗？",
    ]
    for question in demo_questions:
        print(format_fused(question, hybrid_search(question, top_k=5)))
        print("=" * 60)
