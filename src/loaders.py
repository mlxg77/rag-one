"""文档加载：把 .md / .txt / .pdf 统一转换为 {text, metadata} 记录。"""

from pathlib import Path

import pymupdf

# 支持的扩展名（统一小写后比较）
SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf"}

# loaders.py 位于 src/ 下，上跳两级得到项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# txt/md 调用时不传，PDF 调用时传页码
def _make_record(text: str, source: str, page: int | None = None) -> dict:
    """构造统一记录；page 为 None 时不带 page 键。"""
    metadata = {"source": source}
    if page is not None:
        metadata["page"] = page
    return {"text": text, "metadata": metadata}

# txt 加载
def load_txt(path: Path) -> list[dict]:
    """读取纯文本文件（utf-8），返回单条记录。"""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"[警告] 读取失败 {path.name}: {e}")
        return []
    if not text.strip():
        print(f"[警告] 空文档已跳过: {path.name}")
        return []
    return [_make_record(text, path.name)]

# md 加载   
def load_md(path: Path) -> list[dict]:
    """Markdown 按纯文本处理（保留 # 标题标记，阶段三切分要用）。"""
    return load_txt(path)

# pdf 加载
def load_pdf(path: Path) -> list[dict]:
    """逐页提取 PDF 文本，每页一条记录，页码从 1 开始。"""
    try:
        doc = pymupdf.open(path)
    except Exception as e:  # 损坏、加密、伪装成 .pdf 的文件都可能在这里抛异常
        print(f"[警告] PDF 打开失败 {path.name}: {e}")
        return []

    records: list[dict] = []
    with doc:  # 退出时自动 close，不用手写 doc.close()
        for page_no, page in enumerate(doc, start=1):
            text = page.get_text()
            if not text.strip():
                print(f"[警告] 空页已跳过: {path.name} 第 {page_no} 页")
                continue
            records.append(_make_record(text, path.name, page=page_no))

    if not records:
        print(f"[警告] PDF 无可提取文本: {path.name}")
    return records

def load_file(path: Path) -> list[dict]:
    """按扩展名分发到具体加载函数；未知类型跳过。"""
    suffix = path.suffix.lower()
    if suffix == ".md":
        return load_md(path)
    if suffix == ".txt":
        return load_txt(path)
    if suffix == ".pdf":
        return load_pdf(path)
    print(f"[跳过] 不支持的文件类型: {path.name}")
    return []


def load_directory(dir_path: Path) -> list[dict]:
    """扫描目录下所有支持的文件，按文件名排序保证顺序稳定。"""
    records: list[dict] = []
    for p in sorted(dir_path.glob("*")):
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES:
            records.extend(load_file(p))
    return records

def summarize(records: list[dict]) -> None:
    """打印加载统计：文档数、记录数、字符数。"""
    doc_count = len({r["metadata"]["source"] for r in records})
    char_count = sum(len(r["text"]) for r in records)
    print(f"文档数: {doc_count}")
    print(f"记录数: {len(records)}")
    print(f"总字符数: {char_count}")


if __name__ == "__main__":
    raw_dir = PROJECT_ROOT / "data" / "raw"
    records = load_directory(raw_dir)
    print(f"=== 加载目录: {raw_dir} ===")
    summarize(records)