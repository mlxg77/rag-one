"""文档导入入口：一条命令建立（全量重建）向量索引。

用法：
    python -X utf8 ingest.py
"""

from src.config import CHROMA_DIR, DATA_RAW_DIR
from src.indexer import build_index


def main() -> None:
    print(f"=== 建立索引：{DATA_RAW_DIR} -> {CHROMA_DIR} ===")
    stats = build_index()
    print(f"文档数: {stats['docs']}")
    print(f"chunk 数: {stats['chunks']}")
    print(f"集合内向量数: {stats['collection_count']}")
    print("索引已持久化到 storage/chroma，重启后仍然存在。")


if __name__ == "__main__":
    main()