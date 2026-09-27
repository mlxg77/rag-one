"""索引安全重建单元测试：先建后切——任何一步失败，旧索引原封不动。全程离线。

向量库指向 tmp 目录，向量化与加载用替身：不碰网络、不碰真实 storage/chroma。

运行：python -X utf8 -m pytest tests/test_indexer.py -v
"""

import pytest

from src import indexer, vector_store

OLD_ID = "old.md:chunk-0"
NEW_TEXT = "差旅住宿标准：去上海出差，酒店每晚含税最高报销 700 元。" * 40  # 切分后得到多块


def fake_records() -> list[dict]:
    """替身 loader 输出：一条长记录，切分后得到多个 chunk。"""
    return [{"text": NEW_TEXT, "metadata": {"source": "new.md"}}]


def fake_embed(texts: list[str]) -> list[list[float]]:
    """替身向量化：不碰网络，维度固定为 3。"""
    return [[float(len(t) % 10), 1.0, 0.5] for t in texts]


def fake_embed_fail(texts: list[str]) -> list[list[float]]:
    raise RuntimeError("模拟 Embedding API 失败")


@pytest.fixture
def env(tmp_path, monkeypatch):
    """向量库指向临时目录，并预置一份"旧索引"（old.md:chunk-0）。"""
    monkeypatch.setattr(vector_store, "CHROMA_DIR", tmp_path / "chroma")
    monkeypatch.setattr(indexer, "load_directory", lambda _dir: fake_records())
    monkeypatch.setattr(indexer, "embed_texts", fake_embed)

    client = vector_store.get_client()
    old = vector_store.get_collection(client)
    old.upsert(
        ids=[OLD_ID],
        embeddings=[[9.0, 9.0, 9.0]],
        documents=["旧数据"],
        metadatas=[{"source": "old.md"}],
    )
    return client


def ids_of(collection) -> set[str]:
    return set(collection.get()["ids"])


def test_build_switches_to_new_collection(env):
    # 正常路径：新数据接管正式名，旧数据被替换，staging 无残留
    stats = indexer.build_index()
    assert stats["collection_count"] == stats["chunks"] >= 2

    final = vector_store.get_collection(env)
    ids = ids_of(final)
    assert OLD_ID not in ids
    assert all(i.startswith("new.md:chunk-") for i in ids)
    names = {c.name for c in env.list_collections()}
    assert names == {vector_store.COLLECTION_NAME}


def test_embed_failure_keeps_old_index(env, monkeypatch):
    # 向量化失败（最大失败源）：旧索引原封不动
    monkeypatch.setattr(indexer, "embed_texts", fake_embed_fail)
    with pytest.raises(RuntimeError, match="Embedding"):
        indexer.build_index()
    final = vector_store.get_collection(env)
    assert ids_of(final) == {OLD_ID}


def test_upsert_failure_keeps_old_index(env, monkeypatch):
    # staging 写入失败：旧索引原封不动
    def fail_upsert(*args, **kwargs):
        raise RuntimeError("模拟写入失败")

    monkeypatch.setattr(vector_store, "upsert_chunks", fail_upsert)
    with pytest.raises(RuntimeError, match="写入失败"):
        indexer.build_index()
    final = vector_store.get_collection(env)
    assert ids_of(final) == {OLD_ID}


def test_validation_failure_cleans_staging(env, monkeypatch):
    # 校验失败：抛错 + 清理 staging + 旧索引仍在
    monkeypatch.setattr(vector_store, "count", lambda _c: 0)  # 喂一个错误的校验值
    with pytest.raises(RuntimeError, match="校验失败"):
        indexer.build_index()
    final = vector_store.get_collection(env)
    assert ids_of(final) == {OLD_ID}
    names = {c.name for c in env.list_collections()}
    assert indexer.STAGING_COLLECTION not in names


def test_new_collection_queryable_after_switch(env):
    # 接管后的集合可正常查询（切换完整性）
    indexer.build_index()
    final = vector_store.get_collection(env)
    res = final.query(query_embeddings=[[0.0, 1.0, 0.5]], n_results=1, include=["documents"])
    assert res["documents"][0]


def test_first_build_without_old_collection(tmp_path, monkeypatch):
    # 全新环境（无旧集合）：首次构建直接成功
    monkeypatch.setattr(vector_store, "CHROMA_DIR", tmp_path / "chroma")
    monkeypatch.setattr(indexer, "load_directory", lambda _dir: fake_records())
    monkeypatch.setattr(indexer, "embed_texts", fake_embed)
    stats = indexer.build_index()
    assert stats["collection_count"] == stats["chunks"] >= 2
