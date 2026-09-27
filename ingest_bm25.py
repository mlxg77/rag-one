"""BM25 索引构建入口：一条命令从 data/raw 原文重建关键词索引。

用法：
    python -X utf8 ingest_bm25.py
"""

from src.bm25_store import INDEX_PATH, build_index, load_index, save_index
from src.config import DATA_RAW_DIR
from src.loaders import load_directory
from src.splitter import split_records


def rebuild_bm25_index() -> dict:
    """从 data/raw 重建 BM25 索引，并失效进程内缓存；返回统计（供界面复用）。

    与向量索引的「先建后切」同思路：save_index 原子替换——
    构建或写出失败，旧索引文件原封不动。
    """
    records = load_directory(DATA_RAW_DIR)
    chunks = split_records(records)
    index = build_index(chunks)
    save_index(index)
    load_index.cache_clear()  # 关键：重建后清掉进程内旧缓存，检索才会用上新索引
    meta = index["meta"]
    return {
        "docs": len({c["source"] for c in index["chunks"]}),
        "chunks": meta["chunk_count"],
        "terms": meta["term_count"],
        "built_at": meta["built_at"],
        "avgdl": index["avgdl"],
    }


def main() -> None:
    print(f"=== 建立 BM25 索引：{DATA_RAW_DIR} -> {INDEX_PATH} ===")
    stats = rebuild_bm25_index()

    print(f"文档数: {stats['docs']}")
    print(f"chunk 数: {stats['chunks']}")
    print(f"词项数: {stats['terms']}")
    print(f"平均块长: {stats['avgdl']:.1f} tokens")
    print("索引已持久化到 storage/bm25；可用 python -X utf8 -m src.bm25_store 演示检索。")


if __name__ == "__main__":
    main()