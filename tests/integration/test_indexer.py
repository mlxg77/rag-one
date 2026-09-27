"""v2.5 双索引不可变版本与原子发布测试。"""

import json

import pytest

from rag_one.indexing import bm25_store, indexer, manifest, vector_store
from rag_one.indexing.manifest import ManifestError

OLD_ID = "old.md:chunk-0"
NEW_TEXT = "差旅住宿标准：去上海出差，酒店每晚含税最高报销 700 元。" * 40


def fake_records() -> list[dict]:
    return [{"text": NEW_TEXT, "metadata": {"source": "new.md"}}]


def fake_embed(texts: list[str]) -> list[list[float]]:
    return [[float(len(text) % 10), 1.0, 0.5] for text in texts]


def _old_manifest(root, bm25_path) -> dict:
    return {
        "schema_version": manifest.SCHEMA_VERSION,
        "index_version": "old-v1",
        "corpus_sha256": "old-corpus",
        "chunk_size": 800,
        "chunk_overlap": 150,
        "chunk_count": 1,
        "chunk_ids_sha256": manifest.chunk_ids_sha256([OLD_ID]),
        "embedding_model": "fake-embedding",
        "vector_collection": "rag_docs__old_v1",
        "bm25_file": bm25_path.relative_to(root).as_posix(),
        "built_at": "2026-01-01T00:00:00+00:00",
        "git_commit": "test",
    }


@pytest.fixture
def env(tmp_path, monkeypatch):
    root = tmp_path / "project"
    raw = root / "data" / "raw"
    raw.mkdir(parents=True)
    (raw / "new.md").write_text(NEW_TEXT, encoding="utf-8")
    chroma = root / "storage" / "chroma"
    bm25_dir = root / "storage" / "bm25"
    manifest_dir = root / "storage" / "index-manifests"
    active_path = root / "storage" / "active-index.json"

    monkeypatch.setattr(vector_store, "CHROMA_DIR", chroma)
    monkeypatch.setattr(manifest, "MANIFEST_DIR", manifest_dir)
    monkeypatch.setattr(manifest, "ACTIVE_INDEX_PATH", active_path)
    monkeypatch.setattr(indexer, "BM25_DIR", bm25_dir)
    monkeypatch.setattr(indexer, "PROJECT_ROOT", root)
    monkeypatch.setattr(indexer, "load_directory", lambda _raw: fake_records())
    monkeypatch.setattr(indexer, "embed_texts", fake_embed)
    monkeypatch.setattr(indexer, "new_index_version", lambda _hash: "new-v1")

    client = vector_store.get_client()
    old_collection = vector_store.create_collection(client, "rag_docs__old_v1")
    vector_store.upsert_chunks(
        old_collection,
        ids=[OLD_ID],
        texts=["旧数据"],
        metadatas=[{"source": "old.md"}],
        embeddings=[[9.0, 9.0, 9.0]],
    )
    old_bm25_path = bm25_dir / "old-v1.json"
    bm25_store.save_index(
        bm25_store.build_index(
            [{"id": OLD_ID, "text": "旧数据", "metadata": {"source": "old.md"}}]
        ),
        old_bm25_path,
    )
    old = _old_manifest(root, old_bm25_path)
    manifest.write_manifest(old)
    manifest.activate_manifest(old)
    return {"root": root, "raw": raw, "client": client, "old": old}


def _build(env) -> dict:
    return indexer.build_and_publish_indexes(raw_dir=env["raw"])


def _collection_names(env) -> set[str]:
    return {collection.name for collection in env["client"].list_collections()}


def _assert_old_active(env) -> None:
    assert manifest.load_active_manifest()["index_version"] == "old-v1"
    old = vector_store.get_collection(env["client"], "rag_docs__old_v1")
    assert set(vector_store.ids(old)) == {OLD_ID}


def test_success_activates_one_dual_index_version(env):
    stats = _build(env)
    active = manifest.load_active_manifest()

    assert stats["index_version"] == active["index_version"] == "new-v1"
    assert stats["chunks"] == stats["collection_count"] >= 2
    assert active["vector_collection"] == "rag_docs__new_v1"
    assert active["bm25_file"].endswith("storage/bm25/new-v1.json")
    assert {"rag_docs__old_v1", "rag_docs__new_v1"} == _collection_names(env)
    assert (env["root"] / active["bm25_file"]).exists()


def test_embedding_failure_keeps_old_active(env, monkeypatch):
    monkeypatch.setattr(
        indexer,
        "embed_texts",
        lambda _texts: (_ for _ in ()).throw(RuntimeError("模拟 Embedding 失败")),
    )
    with pytest.raises(RuntimeError, match="Embedding"):
        _build(env)
    _assert_old_active(env)
    assert _collection_names(env) == {"rag_docs__old_v1"}


def test_vector_write_failure_keeps_old_active(env, monkeypatch):
    monkeypatch.setattr(
        vector_store,
        "upsert_chunks",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("向量写入失败")),
    )
    with pytest.raises(RuntimeError, match="向量写入"):
        _build(env)
    _assert_old_active(env)
    assert _collection_names(env) == {"rag_docs__old_v1"}


def test_bm25_write_failure_keeps_old_active(env, monkeypatch):
    monkeypatch.setattr(
        indexer,
        "save_index",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("BM25 写入失败")),
    )
    with pytest.raises(RuntimeError, match="BM25"):
        _build(env)
    _assert_old_active(env)
    assert _collection_names(env) == {"rag_docs__old_v1"}


def test_manifest_write_failure_cleans_candidate(env, monkeypatch):
    monkeypatch.setattr(
        indexer,
        "write_manifest",
        lambda _payload: (_ for _ in ()).throw(RuntimeError("manifest 写入失败")),
    )
    with pytest.raises(RuntimeError, match="manifest"):
        _build(env)
    _assert_old_active(env)
    assert _collection_names(env) == {"rag_docs__old_v1"}
    assert not (env["root"] / "storage" / "bm25" / "new-v1.json").exists()


def test_pointer_replace_failure_keeps_old_but_preserves_candidate(env, monkeypatch):
    original_replace = manifest.os.replace

    def fail_active_pointer(source, target):
        if target == manifest.ACTIVE_INDEX_PATH:
            raise OSError("pointer replace 失败")
        return original_replace(source, target)

    monkeypatch.setattr(manifest.os, "replace", fail_active_pointer)
    with pytest.raises(OSError, match="pointer replace"):
        _build(env)
    _assert_old_active(env)
    assert "rag_docs__new_v1" in _collection_names(env)
    assert manifest.manifest_path("new-v1").exists()
    assert (env["root"] / "storage" / "bm25" / "new-v1.json").exists()


def test_vector_bm25_id_mismatch_is_not_activated(env, monkeypatch):
    original = indexer.build_bm25_index

    def mismatched(chunks):
        built = original(chunks)
        built["chunks"][0]["id"] = "wrong.md:chunk-0"
        return built

    monkeypatch.setattr(indexer, "build_bm25_index", mismatched)
    with pytest.raises(indexer.IndexBuildError, match="BM25 索引 chunk ID 不一致"):
        _build(env)
    _assert_old_active(env)


def test_rollback_reactivates_existing_old_version(env):
    _build(env)
    rolled_back = manifest.rollback("old-v1")
    assert rolled_back["index_version"] == "old-v1"
    _assert_old_active(env)


def test_corrupt_active_manifest_is_rejected(env):
    manifest.manifest_path("old-v1").write_text("{broken", encoding="utf-8")
    with pytest.raises(ManifestError, match="manifest 无法读取"):
        manifest.load_active_manifest()


def test_active_pointer_version_mismatch_is_rejected(env):
    pointer = json.loads(manifest.ACTIVE_INDEX_PATH.read_text(encoding="utf-8"))
    pointer["index_version"] = "other-v1"
    manifest.ACTIVE_INDEX_PATH.write_text(json.dumps(pointer), encoding="utf-8")
    with pytest.raises(ManifestError, match="index_version 不一致"):
        manifest.load_active_manifest()
