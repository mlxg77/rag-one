"""评估汇总口径测试。"""

import pytest

from evaluation.evaluate_e2e import summarize as summarize_e2e
from evaluation.evaluate_retrieval import summarize as summarize_retrieval


def retrieval_row(recall, group_recall, complete, latency=10):
    return {
        "recall_at_5": recall,
        "recall_at_10": recall,
        "reciprocal_rank": float(recall) if recall is not None else None,
        "relevant_hit_count": recall,
        "relevant_chunk_ids": ["a"],
        "evidence_group_recall_at_5": group_recall,
        "complete_evidence_at_5": complete,
        "adjacent_chunk_pair_rate_at_5": 0.1,
        "distinct_sources_at_5": 2,
        "context_chars_at_5": 1000,
        "latency_ms": latency,
    }


def test_retrieval_summary_separates_any_hit_and_complete_evidence():
    summary = summarize_retrieval(
        [retrieval_row(1, 0.5, 0, 10), retrieval_row(1, 1.0, 1, 30)]
    )
    assert summary["recall_at_5"] == 1.0
    assert summary["evidence_group_recall_at_5"] == 0.75
    assert summary["complete_evidence_at_5"] == 0.5
    assert summary["latency_ms"]["avg"] == 20.0


def test_retrieval_summary_rejects_no_scored_questions():
    with pytest.raises(ValueError, match="没有可计算"):
        summarize_retrieval([retrieval_row(None, None, None)])


def e2e_row(recall, group_recall, complete, invalid=False):
    return {
        "recall_at_5": recall,
        "evidence_group_recall_at_5": group_recall,
        "complete_evidence_at_5": complete,
        "usage": {"prompt_tokens": 10, "completion_tokens": 2},
        "citation_validation": {
            "invalid_citations": [9] if invalid else [],
            "refusal_has_citations": False,
        },
        "latency_ms": {"retrieve": 5, "generate": 7, "total": 12},
    }


def test_e2e_summary_counts_invalid_citations():
    summary = summarize_e2e(
        [e2e_row(1, 0.5, 0, True), e2e_row(0, 1.0, 1)], "vector"
    )
    assert summary["recall_at_5"] == 0.5
    assert summary["complete_evidence_at_5"] == 0.5
    assert summary["invalid_citation_answers"] == 1
