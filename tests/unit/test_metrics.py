"""证据组指标单元测试。"""

from evaluation.metrics import adjacent_chunk_pair_rate, complete_evidence_at_k, evidence_group_recall


def test_evidence_group_recall_accepts_any_alternative_in_group():
    groups = [["a-1", "a-2"], ["b-1"], ["c-1", "c-2"]]
    assert evidence_group_recall(["noise", "a-2", "c-1"], groups, 5) == 2 / 3


def test_complete_evidence_requires_every_group_within_k():
    groups = [["a"], ["b", "b-alt"]]
    assert complete_evidence_at_k(["a", "b-alt"], groups, 2) == 1
    assert complete_evidence_at_k(["a", "noise", "b"], groups, 2) == 0


def test_evidence_metrics_exclude_questions_without_groups():
    assert evidence_group_recall(["a"], [], 5) is None
    assert complete_evidence_at_k(["a"], [], 5) is None


def test_adjacent_chunk_pair_rate_keeps_pdf_pages_separate():
    ids = [
        "a.md:chunk-0",
        "a.md:chunk-1",
        "a.md:chunk-3",
        "x.pdf:page-1:chunk-0",
        "x.pdf:page-2:chunk-0",
    ]
    assert adjacent_chunk_pair_rate(ids, 5) == 0.1  # 1 个相邻对 / 10 个无序对
