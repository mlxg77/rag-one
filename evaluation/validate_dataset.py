"""校验 regression/holdout 的 JSONL 结构与 active chunk 标注。"""

import argparse
import json
from pathlib import Path

from evaluation.dataset import prepare_questions, validate_questions


def main() -> None:
    parser = argparse.ArgumentParser(description="校验评估集")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.paths:
        questions, chunks = prepare_questions(path)
        result = validate_questions(questions, {chunk["id"] for chunk in chunks})
        print(f"{path}: " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
