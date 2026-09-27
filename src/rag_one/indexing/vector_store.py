"""ChromaDB 本地持久化向量库的读写封装。"""

import chromadb
from chromadb.errors import NotFoundError

from rag_one.config import CHROMA_DIR
from rag_one.indexing.manifest import load_active_manifest


def get_client() -> chromadb.ClientAPI:
    """打开（或创建）本地持久化目录；程序重启后数据仍在。"""
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    # 把向量库固定绑定到磁盘上的 storage/chroma 目录，避免运行时改名。（相当于创建数据库）
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def create_collection(client: chromadb.ClientAPI, name: str) -> chromadb.Collection:
    """创建不可变版本集合；同名已存在时拒绝覆盖。"""
    return client.create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=None,
    )


def get_collection(
    client: chromadb.ClientAPI,
    name: str | None = None,
) -> chromadb.Collection:
    """读取指定集合；省略名称时读取 active manifest 指向的集合。"""
    collection_name = name or load_active_manifest()["vector_collection"]
    return client.get_collection(name=collection_name, embedding_function=None)


def get_or_create_collection(client: chromadb.ClientAPI, name: str) -> chromadb.Collection:
    """兼容旧索引迁移使用；v2.5 正常构建应调用 create_collection。"""
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=None,
    )


def delete_collection(client: chromadb.ClientAPI, name: str) -> None:
    """删除集合；不存在时静默（幂等删除）。"""
    try:
        client.delete_collection(name)
    except NotFoundError:
        pass  # 幂等：没这张表就当删过了


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


def ids(collection: chromadb.Collection) -> list[str]:
    """读取集合内全部 chunk ID，供发布校验使用。"""
    return list(collection.get(include=[])["ids"])
