"""ChromaDB 本地持久化向量库的读写封装。"""

import chromadb
from chromadb.errors import NotFoundError

from src.config import CHROMA_DIR, COLLECTION_NAME


def get_client() -> chromadb.ClientAPI:
    """打开（或创建）本地持久化目录；程序重启后数据仍在。"""
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    # 把向量库固定绑定到磁盘上的 storage/chroma 目录，避免运行时改名。（相当于创建数据库）
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    """获取或创建集合；距离用余弦，不让 Chroma 自带内置向量函数。"""
    # Chroma 里 client 相当于"数据库"，collection 相当于"一张表"。
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # 表内怎么比相似度（仅建表时生效）
        embedding_function=None,             # 向量一律外部传入，Chroma 不碰
    )

# metadata 只在集合真正被新建时生效，后续的修改不会更新。所以要删除并重建集合
def reset_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    """删除并重建集合（全量重建索引用）。"""
    try:
        client.delete_collection(COLLECTION_NAME)
    except NotFoundError:
        pass  # 第一次运行时集合还不存在，忽略
    return get_collection(client)

def upsert_chunks(
    collection: chromadb.Collection,
    ids: list[str],
    texts: list[str],
    metadatas: list[dict],
    embeddings: list[list[float]],
) -> None:
    """按 id 写入；四个列表长度必须一致，相同 id 会被覆盖。"""
    # upsert：是 update + insert 的合成词，语义是"按 id 写入"
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )


def count(collection: chromadb.Collection) -> int:
    """集合内向量条数。"""
    return collection.count()