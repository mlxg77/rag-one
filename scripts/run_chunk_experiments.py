"""串行构建 chunk 参数版本并运行 regression 四模式评估。

该命令会向 `.env` 指定的 Embedding/Rerank 服务发送语料或问题；
只能在已获明确数据出站授权时运行。它不读取 holdout。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from rag_one.config import PROJECT_ROOT
from rag_one.indexing.bm25_store import clear_index_cache
from rag_one.indexing.indexer import build_and_publish_indexes
from rag_one.indexing.manifest import activate_manifest, load_active_manifest

DEFAULT_CONFIGS = ((600, 150), (800, 150), (1000, 150), (800, 80), (800, 220))
MODES = ("vector", "bm25", "hybrid", "hybrid_rerank")


def parse_configs(value: str) -> list[tuple[int, int]]:
    configs: list[tuple[int, int]] = []
    for item in value.split(","):
        try:
            size_text, overlap_text = item.strip().split("/", 1)
            size, overlap = int(size_text), int(overlap_text)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"非法参数 {item!r}，期望 size/overlap") from exc
        if size < 1 or overlap < 0 or overlap >= size:
            raise argparse.ArgumentTypeError(f"非法参数 {item!r}：要求 size > overlap >= 0")
        configs.append((size, overlap))
    if not configs:
        raise argparse.ArgumentTypeError("至少需要一组 chunk 参数")
    return configs


def run_evaluation(mode: str, out: Path, force: bool) -> None:
    command = [
        sys.executable,
        "-X",
        "utf8",
        "-m",
        "evaluation.evaluate_retrieval",
        "--mode",
        mode,
        "--dataset",
        "data/eval/regression.jsonl",
        "--out",
        str(out),
    ]
    if force:
        command.append("--force")
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="v2.5 chunk 四模式真实实验")
    parser.add_argument(
        "--configs",
        type=parse_configs,
        default=list(DEFAULT_CONFIGS),
        help="逗号分隔的 size/overlap，默认运行 T2/T3 五组",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    results_root = PROJECT_ROOT / "data" / "eval" / "results" / "v2.5" / "chunks"
    index_path = results_root / "experiment-index.json"
    expected_outputs = [
        results_root / f"{size}-{overlap}" / f"run-{mode}.json"
        for size, overlap in args.configs
        for mode in MODES
    ]
    existing = [path for path in [index_path, *expected_outputs] if path.exists()]
    if existing and not args.force:
        raise SystemExit(f"实验结果已存在：{existing[0]}（使用 --force 才允许覆盖）")

    starting_manifest = load_active_manifest()
    summaries: list[dict] = []
    try:
        for chunk_size, chunk_overlap in args.configs:
            label = f"{chunk_size}-{chunk_overlap}"
            print(f"\n=== chunk {chunk_size}/{chunk_overlap} ===", flush=True)
            stats = build_and_publish_indexes(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            out_dir = results_root / label
            out_dir.mkdir(parents=True, exist_ok=True)
            for mode in MODES:
                run_evaluation(mode, out_dir / f"run-{mode}.json", args.force)
            summaries.append({"label": label, **stats})
    finally:
        activate_manifest(starting_manifest)
        clear_index_cache()

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"完成 {len(summaries)} 组实验；已恢复 active version {starting_manifest['index_version']}")


if __name__ == "__main__":
    main()
