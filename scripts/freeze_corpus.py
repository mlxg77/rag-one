"""语料冻结：为 data/raw 生成版本记录（文件清单 + SHA256 指纹 + 切分统计）。

用途：v2.5 复查 v2 冻结语料；输出到 data/snapshots/corpus-v2.md。
运行：python -X utf8 -m scripts.freeze_corpus（在项目根目录）
"""

import hashlib
from datetime import date
from pathlib import Path

from rag_one.ingestion.loaders import SUPPORTED_SUFFIXES, load_directory
from rag_one.ingestion.splitter import CHUNK_OVERLAP, CHUNK_SIZE, split_records

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUT_PATH = PROJECT_ROOT / "data" / "snapshots" / "corpus-v2.md"

def sha256_of(path: Path) -> str:
    """文件内容指纹：SHA256 前 16 位。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]

def build_markdown() -> str:
    """收集文件清单、指纹与切分统计，组装成 Markdown 文本。"""
    # 1) 文件清单（只含受支持扩展名 = 实际会被加载的文件）
    files = [
        p
        for p in sorted(RAW_DIR.glob("*"))
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    ]

    # 2) 加载 + 切分
    records = load_directory(RAW_DIR)
    chunks = split_records(records)

    # 3) 每篇的 chunk 数（保序计数）
    per_source: dict[str, int] = {}
    for ch in chunks:
        src = ch["metadata"]["source"]
        per_source[src] = per_source.get(src, 0) + 1

    # 4) 平均长度
    avg_len = sum(len(c["text"]) for c in chunks) / len(chunks)

    # 5) 组装 Markdown
    lines: list[str] = []
    lines.append("# 语料版本记录（v2.0 冻结）")
    lines.append("")
    lines.append(f"- 生成日期：{date.today().isoformat()}")
    lines.append("- 语料目录：data/raw/")
    lines.append(f"- 切分参数：CHUNK_SIZE={CHUNK_SIZE}，CHUNK_OVERLAP={CHUNK_OVERLAP}")
    lines.append("")
    lines.append(
        f"统计：文档 {len(per_source)} 篇（记录 {len(records)} 条）→ "
        f"chunk {len(chunks)} 个，平均 {avg_len:.1f} 字符。"
    )
    lines.append("")
    lines.append("> 本文件是 rag-one v2.0 全部实验共用的语料版本快照；文件指纹为 SHA256 前 16 位。")
    lines.append("> 冻结期内不得新增、重写或替换 data/raw 下的任何文件。")
    lines.append("> 复查方式：重跑 `python -X utf8 -m scripts.freeze_corpus`，比对指纹与统计。")
    lines.append("")
    lines.append("## 文件清单与指纹")
    lines.append("")
    lines.append("| 文件 | 字节数 | SHA256（前 16 位） |")
    lines.append("|---|---:|---|")
    for p in files:
        lines.append(f"| {p.name} | {p.stat().st_size} | `{sha256_of(p)}` |")
    lines.append("")
    lines.append("## 每篇 chunk 分布")
    lines.append("")
    lines.append("| 来源 | chunk 数 |")
    lines.append("|---|---:|")
    for src, n in per_source.items():
        lines.append(f"| {src} | {n} |")
    lines.append("")
    return "\n".join(lines)

if __name__ == "__main__":
    report = build_markdown()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"已写入：{OUT_PATH}")
