"""端到端结果的人工答案/引用/拒答/幻觉判定与汇总。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


class ReviewError(ValueError):
    """人工判定缺失或口径不合法。"""


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ReviewError(f"{path}:{line_no} JSON 无法解析：{exc}") from exc
        if not isinstance(row, dict):
            raise ReviewError(f"{path}:{line_no} 必须是 JSON object")
        rows.append(row)
    return rows


def review_template(result: dict) -> list[dict]:
    return [
        {
            "question_id": row["question_id"],
            "answer_correct": None,
            "citation_correct": None,
            "citation_supported_count": None,
            "citation_total_count": len(row["citations"]),
            "refusal_correct": None,
            "hallucination": None,
            "notes": "",
        }
        for row in result["questions"]
    ]


def summarize_review(result: dict, reviews: list[dict]) -> dict:
    expected_ids = [row["question_id"] for row in result["questions"]]
    by_id: dict[str, dict] = {}
    errors: list[str] = []
    for row in reviews:
        qid = row.get("question_id")
        if qid in by_id:
            errors.append(f"重复判定：{qid}")
        by_id[qid] = row
    if set(by_id) != set(expected_ids):
        errors.append(
            f"判定题号与结果不一致："
            f"missing={sorted(set(expected_ids) - set(by_id))} "
            f"extra={sorted(set(by_id) - set(expected_ids))}"
        )

    citation_rows: list[dict] = []
    refusal_rows: list[dict] = []
    for qid in expected_ids:
        row = by_id.get(qid)
        if row is None:
            continue
        for field in ("answer_correct", "hallucination"):
            if not isinstance(row.get(field), bool):
                errors.append(f"{qid}: {field} 必须是 boolean")
        citation_correct = row.get("citation_correct")
        if citation_correct is not None:
            if not isinstance(citation_correct, bool):
                errors.append(f"{qid}: citation_correct 必须是 boolean 或 null")
            else:
                citation_rows.append(row)
            supported = row.get("citation_supported_count")
            total = row.get("citation_total_count")
            if not isinstance(supported, int) or isinstance(supported, bool):
                errors.append(f"{qid}: citation_supported_count 必须是整数")
            if not isinstance(total, int) or isinstance(total, bool) or total < 1:
                errors.append(f"{qid}: citation_total_count 必须是正整数")
            elif isinstance(supported, int) and not isinstance(supported, bool) and not 0 <= supported <= total:
                errors.append(f"{qid}: 支持引用数不能超过引用总数")
        refusal_correct = row.get("refusal_correct")
        if refusal_correct is not None:
            if not isinstance(refusal_correct, bool):
                errors.append(f"{qid}: refusal_correct 必须是 boolean 或 null")
            else:
                refusal_rows.append(row)
    if errors:
        raise ReviewError("\n".join(errors))

    ordered = [by_id[qid] for qid in expected_ids]
    total_supported = sum(row["citation_supported_count"] for row in citation_rows)
    total_citations = sum(row["citation_total_count"] for row in citation_rows)
    return {
        "question_count": len(ordered),
        "answer_accuracy": sum(row["answer_correct"] for row in ordered) / len(ordered),
        "strict_citation_accuracy": (
            sum(row["citation_correct"] for row in citation_rows) / len(citation_rows)
            if citation_rows else None
        ),
        "citation_block_precision": total_supported / total_citations if total_citations else None,
        "refusal_accuracy": (
            sum(row["refusal_correct"] for row in refusal_rows) / len(refusal_rows)
            if refusal_rows else None
        ),
        "hallucination_count": sum(row["hallucination"] for row in ordered),
        "citation_scored_count": len(citation_rows),
        "refusal_scored_count": len(refusal_rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="生成或汇总 E2E 人工判定")
    parser.add_argument("result", type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--init", type=Path, help="生成待填写 JSONL 模板")
    group.add_argument("--review", type=Path, help="读取已填写 JSONL 并汇总")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    if args.init:
        rows = review_template(result)
        args.init.parent.mkdir(parents=True, exist_ok=True)
        args.init.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
        print(f"已生成判定模板：{args.init}")
        return
    summary = summarize_review(result, load_jsonl(args.review))
    rendered = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
