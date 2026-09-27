"""BM25 索引构建入口：一条命令从 data/raw 原文重建关键词索引。

用法：
    python -X utf8 ingest_bm25.py
"""

from src.bm25_store import INDEX_PATH, build_index, save_index
from src.config import DATA_RAW_DIR
from src.loaders import load_directory
from src.splitter import split_records


def main() -> None:
    print(f"=== 建立 BM25 索引：{DATA_RAW_DIR} -> {INDEX_PATH} ===")
    records = load_directory(DATA_RAW_DIR)
    chunks = split_records(records)
    index = build_index(chunks)
    save_index(index)

    meta = index["meta"]
    doc_count = len({c["source"] for c in index["chunks"]})
    print(f"文档数: {doc_count}")
    print(f"chunk 数: {meta['chunk_count']}")
    print(f"词项数: {meta['term_count']}")
    print(f"平均块长: {index['avgdl']:.1f} tokens")
    print("索引已持久化到 storage/bm25；可用 python -X utf8 -m src.bm25_store 演示检索。")


if __name__ == "__main__":
    main()