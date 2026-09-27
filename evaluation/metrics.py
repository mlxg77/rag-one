"""检索评估指标：全部是纯函数——不读文件、不碰网络、不依赖全局状态。"""

import math


def hit_rank(hit_ids: list[str], relevant_ids: list[str]) -> int | None:
    """第一个相关块在命中列表中的排名（从 1 起）；一个都没命中返回 None。"""
    rel = set(relevant_ids)
    for i, cid in enumerate(hit_ids, start=1):
        if cid in rel:
            return i
    return None


def recall_at_k(hit_ids: list[str], relevant_ids: list[str], k: int) -> int:
    """题级 Recall@K（二值 1/0）：前 K 个命中里是否至少有一个相关块。

    只对 relevant_ids 非空的题调用；拒答题（无标注）不参与统计。
    """
    return 1 if hit_rank(hit_ids[:k], relevant_ids) is not None else 0


def relevant_hit_count(hit_ids: list[str], relevant_ids: list[str], k: int | None = None) -> int:
    """前 K 个命中里含有的相关块个数（k=None 表示不截断），用于块级覆盖诊断。"""
    rel = set(relevant_ids)
    window = hit_ids if k is None else hit_ids[:k]
    return sum(1 for cid in window if cid in rel)


def reciprocal_rank(hit_ids: list[str], relevant_ids: list[str], k: int) -> float:
    """RR@K：第一个相关块排名的倒数（1/rank）；K 名之外或未命中记 0.0。"""
    rank = hit_rank(hit_ids[:k], relevant_ids)
    return 1.0 / rank if rank is not None else 0.0


def percentile(values: list[float], p: float) -> float:
    """nearest-rank 百分位：升序排列后取第 ceil(p% × n) 个（从 1 起数）。"""
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = math.ceil(p / 100 * len(ordered)) - 1
    return ordered[max(idx, 0)]