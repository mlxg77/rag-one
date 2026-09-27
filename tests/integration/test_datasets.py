"""仓库内 regression/holdout 与当前 800/150 切分的一致性测试。"""

from collections import Counter

import pytest

from evaluation.dataset import (
    HOLDOUT_PATH,
    REGRESSION_PATH,
    load_questions,
    prepare_questions,
    validate_questions,
)
from rag_one.config import DATA_RAW_DIR
from rag_one.ingestion.loaders import load_directory
from rag_one.ingestion.splitter import split_records


def current_chunk_ids() -> set[str]:
    return {chunk["id"] for chunk in split_records(load_directory(DATA_RAW_DIR))}


def test_regression_dataset_has_32_valid_questions():
    questions = load_questions(REGRESSION_PATH)
    summary = validate_questions(questions, current_chunk_ids())
    assert summary["question_count"] == 32


def test_holdout_dataset_is_frozen_separate_and_has_required_mix():
    questions = load_questions(HOLDOUT_PATH)
    summary = validate_questions(questions, current_chunk_ids())
    counts = Counter(question["type"] for question in questions)
    assert summary["question_count"] == 15
    assert counts == {
        "keyword": 2,
        "semantic": 3,
        "confusable": 2,
        "multi_evidence": 4,
        "unanswerable": 4,
    }
    assert {q["id"] for q in questions}.isdisjoint(
        {q["id"] for q in load_questions(REGRESSION_PATH)}
    )


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"),
    [(600, 150), (800, 150), (1000, 150), (800, 80), (800, 220)],
)
def test_evidence_anchors_resolve_for_every_chunk_experiment(chunk_size, chunk_overlap):
    questions, chunks = prepare_questions(
        REGRESSION_PATH,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    assert len(questions) == 32
    assert all(question["evidence_groups"] for question in questions if question["id"] != "q24")
    assert chunks
