"""索引构建：加载 -> 切分 -> 向量化 -> 写入 ChromaDB。

v2.0 阶段七：全量重建采用「先建后切」——先写 staging 集合并校验，
通过后才删除旧集合并改名接管；任何一步失败，旧索引原封不动。
"""

import hashlib
from pathlib import Path

from src import vector_store
from src.config import COLLECTION_NAME, DATA_RAW_DIR
from src.embeddings import embed_texts
from src.loaders import load_directory
from src.splitter import split_records

# 临时集合名：由正式集合名派生（名称单一出处仍是 config.COLLECTION_NAME）
STAGING_COLLECTION = COLLECTION_NAME + "__staging"

# 内容哈希：用于增量索引
def _content_hash(text: str) -> str:
    """chunk 内容哈希（先存着，为将来做增量索引用）。"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def build_index(raw_dir: Path = DATA_RAW_DIR) -> dict:
    """全量重建索引（先建后切：失败保留旧索引）。

    顺序刻意设计：最易失败的外部调用（向量化）放在触碰旧索引之前——
    1) 加载 + 切分；2) 全量向量化（旧索引无损）；3) 写入 staging 集合；
    4) 校验 staging；5) 删旧集合 + staging 改名接管；6) 统计。
    """
    # 1) 加载 + 切分
    records = load_directory(raw_dir)
    chunks = split_records(records)
    if not chunks:
        raise RuntimeError(f"没有从 {raw_dir} 加载到任何文档，请检查目录")

    # 2) 全量向量化：最大失败源（外部 API）；此刻旧索引完全未动
    embeddings = embed_texts([c["text"] for c in chunks])

    # 3) 写入 staging 集合（先清理上次可能残留的 staging，保证从干净状态写入）
    client = vector_store.get_client()
    vector_store.reset_collection(client, name=STAGING_COLLECTION)
    staging = vector_store.get_collection(client, name=STAGING_COLLECTION)
    metadatas = [{**c["metadata"], "content_hash": _content_hash(c["text"])} for c in chunks]
    vector_store.upsert_chunks(
        staging,
        ids=[c["id"] for c in chunks],
        texts=[c["text"] for c in chunks],
        metadatas=metadatas,
        embeddings=embeddings,
    )

    # 4) 校验 staging：条数一致 + 可读；失败则清理 staging 并报错（旧索引仍在）
    staged_count = vector_store.count(staging)
    if staged_count != len(chunks):
        vector_store.delete_collection(client, STAGING_COLLECTION)
        raise RuntimeError(
            f"staging 校验失败：写入 {staged_count} 条 ≠ 预期 {len(chunks)} 条；已保留原索引"
        )
    staging.get(limit=1, include=["metadatas"])  # 可读性探针：数据损坏时在此直接报错

    # 5) 切换：删旧集合 -> staging 改名接管（两步均为本地操作，窗口极小）
    vector_store.delete_collection(client, COLLECTION_NAME)
    vector_store.rename_collection(staging, COLLECTION_NAME)

    # 6) 统计（重新按正式名获取，顺带验证切换后的集合可正常使用）
    final = vector_store.get_collection(client)
    return {
        "docs": len({r["metadata"]["source"] for r in records}),
        "chunks": len(chunks),
        "collection_count": vector_store.count(final),
    }