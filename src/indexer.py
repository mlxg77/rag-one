"""索引构建：加载 -> 切分 -> 向量化 -> 写入 ChromaDB（第一版全量重建）。"""

import hashlib
from pathlib import Path

from src import vector_store
from src.config import DATA_RAW_DIR
from src.embeddings import embed_texts
from src.loaders import load_directory
from src.splitter import split_records

# 内容哈希：用于增量索引
def _content_hash(text: str) -> str:
    """chunk 内容哈希（先存着，为将来做增量索引用）。"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def build_index(raw_dir: Path = DATA_RAW_DIR) -> dict:
    """全量重建索引：先删旧集合，再加载/切分/向量化/写入。"""
    # 1) 加载 + 切分
    records = load_directory(raw_dir)
    chunks = split_records(records)
    if not chunks:
        raise RuntimeError(f"没有从 {raw_dir} 加载到任何文档，请检查目录")

    # 2) 打开向量库，先删后建（全量重建）
    client = vector_store.get_client()
    collection = vector_store.reset_collection(client)

    # 3) 向量化（分批逻辑在 embed_texts 内部）
    embeddings = embed_texts([c["text"] for c in chunks])

    # 4) 写入：metadata 里补一个内容哈希
    metadatas = [{**c["metadata"], "content_hash": _content_hash(c["text"])} for c in chunks]
    vector_store.upsert_chunks(
        collection,
        ids=[c["id"] for c in chunks],
        texts=[c["text"] for c in chunks],
        metadatas=metadatas,
        embeddings=embeddings,
    )

    # 5) 返回统计
    return {
        "docs": len({r["metadata"]["source"] for r in records}),
        "chunks": len(chunks),
        "collection_count": vector_store.count(collection),
    }