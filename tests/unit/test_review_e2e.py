"""E2E 人工判定汇总口径测试。"""

import pytest

from evaluation.review_e2e import ReviewError, review_template, summarize_review


RESULT = {
    "questions": [
        {"question_id": "q1", "citations": [1, 2]},
        {"question_id": "q2", "citations": []},
    ]
}


def test_review_template_uses_structural_citation_count():
    rows = review_template(RESULT)
    assert rows[0]["citation_total_count"] == 2
    assert rows[1]["citation_total_count"] == 0


def test_human_review_summary_metrics():
    reviews = [
        {
            "question_id": "q1",
            "answer_correct": True,
            "citation_correct": False,
            "citation_supported_count": 1,
            "citation_total_count": 2,
            "refusal_correct": None,
            "hallucination": False,
        },
        {
            "question_id": "q2",
            "answer_correct": True,
            "citation_correct": None,
            "citation_supported_count": None,
            "citation_total_count": 0,
            "refusal_correct": True,
            "hallucination": False,
        },
    ]
    summary = summarize_review(RESULT, reviews)
    assert summary["answer_accuracy"] == 1.0
    assert summary["strict_citation_accuracy"] == 0.0
    assert summary["citation_block_precision"] == 0.5
    assert summary["refusal_accuracy"] == 1.0
    assert summary["hallucination_count"] == 0


def test_review_requires_every_question_and_boolean_judgments():
    with pytest.raises(ReviewError, match="判定题号"):
        summarize_review(RESULT, [])
