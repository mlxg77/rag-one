"""文本切分：把 loader 记录切成带重叠的 chunk，并生成唯一 ID。"""

from pathlib import Path

from src.loaders import PROJECT_ROOT, load_directory

CHUNK_SIZE = 800      # 目标块大小（字符）
CHUNK_OVERLAP = 150   # 相邻块重叠字符数

# 文本切分 - 核心功能
def split_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
    """把长文本切成带重叠的块；优先在段落/换行/句号处断开。"""
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)  # 窗口右端（不越界）
        if end < n:
            window = text[start:end]
            for sep in ("\n\n", "\n", "。"):
                pos = window.rfind(sep)          # 从右往左找第一个匹配的分隔符
                if pos > chunk_size // 2:        # 断点必须在窗口后半段，否则不切
                    end = start + pos + len(sep) # 断在分隔符之后
                    break
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        start = max(end - chunk_overlap, start + 1)  # 回退 overlap 形成重叠；max 防死循环
    return chunks

# 实际应用：把 loader 记录切成 chunk 记录，并记录元数据
def split_records(records: list[dict]) -> list[dict]:
    """把 loader 记录列表切成 chunk 记录列表。"""
    out: list[dict] = []
    for rec in records:
        source = rec["metadata"]["source"]
        page = rec["metadata"].get("page")   # txt/md 没有这个键，返回 None
        for idx, piece in enumerate(split_text(rec["text"])):
            base = f"{source}:page-{page}" if page is not None else source
            metadata = {"source": source, "chunk_index": idx}
            if page is not None:
                metadata["page"] = page
            out.append({"id": f"{base}:chunk-{idx}", "text": piece, "metadata": metadata})
    return out

def summarize(chunks: list[dict]) -> None:
    """打印 chunk 数量和平均长度。"""
    if not chunks:
        print("chunk 数量: 0")
        return
    avg = sum(len(c["text"]) for c in chunks) / len(chunks)
    print(f"chunk 数量: {len(chunks)}")
    print(f"平均长度: {avg:.1f} 字符")


if __name__ == "__main__":
    # 1) 真实数据：加载 -> 切分 -> 统计
    records = load_directory(PROJECT_ROOT / "data" / "raw")
    chunks = split_records(records)
    summarize(chunks)

    # 2) 合成长文本演示：直观观察边界切分和重叠
    demo = "第一段内容。" * 100 + "\n\n" + "第二段内容。" * 100
    pieces = split_text(demo)
    print(f"\n合成文本 {len(demo)} 字符 -> {len(pieces)} 块")
    for i, p in enumerate(pieces):
        print(f"  块 {i}: {len(p)} 字符")