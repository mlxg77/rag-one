"""评估集结构、来源与证据组校验。"""

import pytest

from evaluation.dataset import DatasetValidationError, validate_questions


def valid_question() -> dict:
    return {
        "id": "q1",
        "question": "问题",
        "expected_answer": "答案",
        "expected_sources": ["a.md"],
        "relevant_chunk_ids": ["a.md:chunk-0", "a.md:chunk-1"],
        "evidence_groups": [["a.md:chunk-0"], ["a.md:chunk-1"]],
        "type": "multi_evidence",
    }


def test_validate_questions_reports_counts_and_types():
    result = validate_questions(
        [valid_question()], {"a.md:chunk-0", "a.md:chunk-1"}
    )
    assert result == {
        "question_count": 1,
        "with_relevant_chunks": 1,
        "with_evidence_groups": 1,
        "types": ["multi_evidence"],
    }


def test_empty_dataset_is_rejected():
    with pytest.raises(DatasetValidationError, match="不能为空"):
        validate_questions([])


def test_unknown_chunk_source_and_group_outside_relevant_are_rejected():
    question = valid_question()
    question["expected_sources"] = ["missing.md"]
    question["evidence_groups"] = [["outside.md:chunk-0"]]
    with pytest.raises(DatasetValidationError) as exc:
        validate_questions(question and [question], {"a.md:chunk-0", "a.md:chunk-1"})
    message = str(exc.value)
    assert "不在 relevant_chunk_ids" in message
    assert "不存在的 chunk" in message
    assert "不存在的来源" in message


def test_duplicate_question_id_and_empty_question_are_rejected():
    first = valid_question()
    second = valid_question()
    second["question"] = " "
    with pytest.raises(DatasetValidationError) as exc:
        validate_questions([first, second])
    assert "重复题号" in str(exc.value)
    assert "question 不能为空" in str(exc.value)
