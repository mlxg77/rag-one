"""RRF（Reciprocal Rank Fusion）融合：把多路检索的名次合成一个统一排名。

核心公式：RRF(d) = Σ 1 / (k + rank_i(d))
- 只用排名、不用原始分数——向量相似度与 BM25 分数不在同一量纲，不能直接相加；
- k（默认 60）压平头部差距，让「两路都认可」比「单路排第一」更有分量；
- 同一 chunk 多路命中则各路的 1/(k+rank) 相加（按 chunk id 去重）；
- 只在单路命中的 chunk 照常保留，只由该路贡献分数，另一路排名记 None。

纯函数模块：不读盘、不碰网络，方便单测与人工复算。
"""

RRF_K = 60  # 融合常数（v2.0 规划起点值，属打分参数）


def rrf_fuse(rank_lists: dict[str, list[dict]], top_k: int = 10, k: int = RRF_K) -> list[dict]:
    """融合多路检索结果，返回统一排名的 Top-K。

    rank_lists：{"路名": [该路命中，按 rank 升序], ...}，
    每路命中至少含 id / rank / score（retrieve 与 bm25 search 的结构已对齐）。
    返回的每个 chunk：公共字段（id / source / page / text / score / rank）
    + 各路附加字段「<路名>_rank」与「<路名>_score」（未命中该路时为 None）。
    """
    if top_k < 1:
        raise ValueError(f"top_k 必须 >= 1，收到 {top_k}")

    fused: dict[str, dict] = {}  # chunk id -> 融合条目（同 id 只保留一条）

    for path_name, hits in rank_lists.items():
        for hit in hits:
            # 首次遇到该 chunk：落地公共字段（两路来自同一份切分结果，source/text 必然一致）
            entry = fused.setdefault(
                hit["id"],
                {
                    "id": hit["id"],
                    "source": hit["source"],
                    "page": hit["page"],
                    "text": hit["text"],
                    "score": 0.0,
                },
            )
            entry["score"] += 1.0 / (k + hit["rank"])   # 本轮贡献的 RRF 分
            entry[f"{path_name}_rank"] = hit["rank"]    # 保留原始排名
            entry[f"{path_name}_score"] = hit["score"]  # 保留原始分数

    # 某路未命中的 chunk：把该路的字段显式补 None，消费方（评估、界面）不用 .get 兜底
    for entry in fused.values():
        for path_name in rank_lists:
            entry.setdefault(f"{path_name}_rank", None)
            entry.setdefault(f"{path_name}_score", None)

    # 融合分降序；同分按 chunk id 升序兜底（与 bm25_store 的并列处理一致）
    ranked = sorted(fused.values(), key=lambda e: (-e["score"], e["id"]))[:top_k]

    results: list[dict] = []
    for rank, entry in enumerate(ranked, start=1):
        entry["rank"] = rank
        results.append(entry)
    return results