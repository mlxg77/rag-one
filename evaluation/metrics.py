"""检索评估指标：全部是纯函数——不读文件、不碰网络、不依赖全局状态。"""

import math
import re

CHUNK_ID_RE = re.compile(r"^(.*):chunk-(\d+)$")


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


def evidence_group_recall(
    hit_ids: list[str], evidence_groups: list[list[str]], k: int
) -> float | None:
    """Top-K 命中的必要证据组比例；同组内任一 chunk 命中即满足该组。"""
    if not evidence_groups:
        return None
    window = set(hit_ids[:k])
    matched = sum(1 for group in evidence_groups if window.intersection(group))
    return matched / len(evidence_groups)


def complete_evidence_at_k(
    hit_ids: list[str], evidence_groups: list[list[str]], k: int
) -> int | None:
    """Top-K 是否命中全部必要证据组；无证据组的问题返回 None。"""
    recall = evidence_group_recall(hit_ids, evidence_groups, k)
    return None if recall is None else int(recall == 1.0)


def adjacent_chunk_pair_rate(hit_ids: list[str], k: int) -> float:
    """Top-K 中同一记录的相邻 chunk 对占全部无序对的比例。

    `source:page-N` 会保留在 chunk 前缀中，因此 PDF 不会把不同页的
    `chunk-0` 误判为相邻块。
    """
    parsed: list[tuple[str, int]] = []
    for chunk_id in hit_ids[:k]:
        match = CHUNK_ID_RE.match(chunk_id)
        if match:
            parsed.append((match.group(1), int(match.group(2))))
        else:
            parsed.append((chunk_id, -1))
    pair_count = len(parsed) * (len(parsed) - 1) // 2
    if pair_count == 0:
        return 0.0
    adjacent = 0
    for left in range(len(parsed)):
        for right in range(left + 1, len(parsed)):
            left_prefix, left_number = parsed[left]
            right_prefix, right_number = parsed[right]
            if left_prefix == right_prefix and abs(left_number - right_number) == 1:
                adjacent += 1
    return adjacent / pair_count


def percentile(values: list[float], p: float) -> float:
    """nearest-rank 百分位：升序排列后取第 ceil(p% × n) 个（从 1 起数）。"""
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = math.ceil(p / 100 * len(ordered)) - 1
    return ordered[max(idx, 0)]
