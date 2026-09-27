"""评估集加载、证据组归一化与结构校验。"""

from __future__ import annotations

import json
from pathlib import Path

from rag_one.config import PROJECT_ROOT
from rag_one.indexing.bm25_store import load_index
from rag_one.ingestion.loaders import load_directory
from rag_one.ingestion.splitter import CHUNK_OVERLAP, CHUNK_SIZE, split_records

REGRESSION_PATH = PROJECT_ROOT / "data" / "eval" / "regression.jsonl"
HOLDOUT_PATH = PROJECT_ROOT / "data" / "eval" / "holdout.jsonl"
EVIDENCE_ANCHORS_PATH = PROJECT_ROOT / "data" / "eval" / "evidence-anchors.json"

REQUIRED_FIELDS = {
    "id",
    "question",
    "expected_answer",
    "expected_sources",
    "relevant_chunk_ids",
    "type",
}


class DatasetValidationError(ValueError):
    """评估集结构或 chunk 标注非法。"""


def evidence_groups_of(question: dict) -> list[list[str]]:
    """兼容旧标注：无 evidence_groups 时把全部 relevant IDs 视为一组替代证据。"""
    groups = question.get("evidence_groups")
    if groups is None:
        relevant = question.get("relevant_chunk_ids", [])
        return [list(relevant)] if relevant else []
    if not isinstance(groups, list):
        return []
    return [list(group) for group in groups]


def load_questions(path: Path = REGRESSION_PATH) -> list[dict]:
    if not path.exists():
        raise DatasetValidationError(f"评估集不存在：{path}")
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise DatasetValidationError(f"{path}:{line_no} JSON 无法解析：{exc}") from exc
    return rows


def load_evidence_anchors(path: Path = EVIDENCE_ANCHORS_PATH) -> dict[str, list[list[str]]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DatasetValidationError(f"证据锚点文件不存在：{path}") from exc
    except json.JSONDecodeError as exc:
        raise DatasetValidationError(f"证据锚点 JSON 无法解析：{exc}") from exc
    if not isinstance(payload, dict):
        raise DatasetValidationError("证据锚点顶层必须是 JSON object")
    return payload


def validate_evidence_anchors(
    questions: list[dict],
    anchors: dict[str, list[list[str]]],
    chunks: list[dict],
) -> dict:
    errors: list[str] = []
    for question in questions:
        qid = question.get("id")
        if qid not in anchors:
            errors.append(f"{qid}: 缺少证据锚点")
            continue
        groups = anchors[qid]
        if not isinstance(groups, list):
            errors.append(f"{qid}: 证据锚点必须是二维数组")
            continue
        if question.get("relevant_chunk_ids") and not groups:
            errors.append(f"{qid}: 有证据标注但锚点为空")
        for group_no, group in enumerate(groups, start=1):
            if not isinstance(group, list) or not group or not all(
                isinstance(anchor, str) and anchor.strip() for anchor in group
            ):
                errors.append(f"{qid}: 锚点组 {group_no} 必须是非空字符串数组")
                continue
            if not any(any(anchor in chunk["text"] for anchor in group) for chunk in chunks):
                errors.append(f"{qid}: 锚点组 {group_no} 在冻结语料中无匹配：{group}")
    if errors:
        raise DatasetValidationError("\n".join(errors))
    return {
        "question_count": len(questions),
        "anchored_question_count": sum(bool(anchors[q["id"]]) for q in questions),
        "evidence_fact_count": sum(len(anchors[q["id"]]) for q in questions),
    }


def apply_evidence_anchors(
    questions: list[dict],
    anchors: dict[str, list[list[str]]],
    chunks: list[dict],
) -> list[dict]:
    """把不受 chunk 参数影响的文本锚点解析为当前切分下的 chunk ID。"""
    resolved: list[dict] = []
    for question in questions:
        groups: list[list[str]] = []
        for anchor_group in anchors[question["id"]]:
            ids = [
                chunk["id"]
                for chunk in chunks
                if any(anchor in chunk["text"] for anchor in anchor_group)
            ]
            if not ids:
                raise DatasetValidationError(
                    f"{question['id']}: 当前 chunk 参数下无法定位证据锚点：{anchor_group}"
                )
            groups.append(ids)
        relevant = list(dict.fromkeys(chunk_id for group in groups for chunk_id in group))
        resolved.append(
            {
                **question,
                "relevant_chunk_ids": relevant,
                "evidence_groups": groups,
                "evidence_anchor_groups": anchors[question["id"]],
            }
        )
    return resolved


def prepare_questions(
    path: Path,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> tuple[list[dict], list[dict]]:
    """校验冻结标注，再将证据锚点映射到指定切分参数。"""
    records = load_directory(PROJECT_ROOT / "data" / "raw")
    reference_chunks = split_records(records)
    questions = load_questions(path)
    validate_questions(questions, {chunk["id"] for chunk in reference_chunks})
    anchors = load_evidence_anchors()
    validate_evidence_anchors(questions, anchors, reference_chunks)
    active_chunks = split_records(
        records,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    resolved = apply_evidence_anchors(questions, anchors, active_chunks)
    validate_questions(resolved, {chunk["id"] for chunk in active_chunks})
    return resolved, active_chunks


def validate_questions(questions: list[dict], known_chunk_ids: set[str] | None = None) -> dict:
    if not questions:
        raise DatasetValidationError("评估集不能为空")
    errors: list[str] = []
    ids: set[str] = set()
    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            errors.append(f"第 {index} 题必须是 JSON object")
            continue
        missing = REQUIRED_FIELDS - question.keys()
        if missing:
            errors.append(f"第 {index} 题缺字段：{sorted(missing)}")
            continue
        qid = question["id"]
        if not isinstance(qid, str) or not qid.strip():
            errors.append(f"第 {index} 题 id 必须是非空字符串")
            continue
        if qid in ids:
            errors.append(f"重复题号：{qid}")
        ids.add(qid)
        if not isinstance(question["question"], str) or not question["question"].strip():
            errors.append(f"{qid}: question 不能为空")
        if not isinstance(question["expected_answer"], str) or not question["expected_answer"].strip():
            errors.append(f"{qid}: expected_answer 不能为空")
        if not isinstance(question["type"], str) or not question["type"].strip():
            errors.append(f"{qid}: type 必须是非空字符串")
        sources = question["expected_sources"]
        if not isinstance(sources, list) or not all(isinstance(source, str) for source in sources):
            errors.append(f"{qid}: expected_sources 必须是字符串数组")
            sources = []
        relevant = question["relevant_chunk_ids"]
        if not isinstance(relevant, list) or not all(isinstance(cid, str) for cid in relevant):
            errors.append(f"{qid}: relevant_chunk_ids 必须是字符串数组")
            continue
        if len(relevant) != len(set(relevant)):
            errors.append(f"{qid}: relevant_chunk_ids 含重复值")
        raw_groups = question.get("evidence_groups")
        if raw_groups is not None and not isinstance(raw_groups, list):
            errors.append(f"{qid}: evidence_groups 必须是数组")
            groups = []
        elif raw_groups is not None:
            groups = []
            for group_no, raw_group in enumerate(raw_groups, start=1):
                if not isinstance(raw_group, list):
                    errors.append(f"{qid}: evidence_groups[{group_no}] 必须是数组")
                    continue
                groups.append(raw_group)
        else:
            groups = evidence_groups_of(question)
        for group_no, group in enumerate(groups, start=1):
            if not group or not all(isinstance(cid, str) for cid in group):
                errors.append(f"{qid}: evidence_groups[{group_no}] 必须是非空字符串数组")
            elif len(group) != len(set(group)):
                errors.append(f"{qid}: evidence_groups[{group_no}] 含重复值")
            unknown_to_question = sorted(set(group) - set(relevant))
            if unknown_to_question:
                errors.append(
                    f"{qid}: evidence_groups[{group_no}] 不在 relevant_chunk_ids 中："
                    f"{unknown_to_question}"
                )
        annotated = set(relevant)
        for group in groups:
            annotated.update(group)
        if known_chunk_ids is not None:
            unknown = sorted(annotated - known_chunk_ids)
            if unknown:
                errors.append(f"{qid}: 标注了不存在的 chunk：{unknown}")
            known_sources = {chunk_id.split(":", 1)[0] for chunk_id in known_chunk_ids}
            unknown_sources = sorted(set(sources) - known_sources)
            if unknown_sources:
                errors.append(f"{qid}: 标注了不存在的来源：{unknown_sources}")
    if errors:
        raise DatasetValidationError("\n".join(errors))
    return {
        "question_count": len(questions),
        "with_relevant_chunks": sum(bool(q["relevant_chunk_ids"]) for q in questions),
        "with_evidence_groups": sum(bool(evidence_groups_of(q)) for q in questions),
        "types": sorted({q["type"] for q in questions}),
    }


def active_chunk_ids() -> set[str]:
    return {chunk["id"] for chunk in load_index()["chunks"]}
