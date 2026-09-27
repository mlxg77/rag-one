"""项目状态校验的不一致检测。"""

import pytest

from rag_one import state
from rag_one.config import EMBEDDING_MODEL
from rag_one.indexing.manifest import chunk_ids_sha256


IDS = ["a.md:chunk-0", "a.md:chunk-1"]


@pytest.fixture
def verified_state(monkeypatch):
    manifest = {
        "index_version": "v-test",
        "corpus_sha256": "corpus-hash",
        "chunk_ids_sha256": chunk_ids_sha256(IDS),
        "chunk_size": 800,
        "chunk_overlap": 150,
        "chunk_count": 2,
        "vector_collection": "rag_docs__v_test",
        "bm25_file": "storage/bm25/v-test.json",
        "embedding_model": EMBEDDING_MODEL,
    }
    chunks = [
        {"id": chunk_id, "text": chunk_id, "metadata": {"source": "a.md"}}
        for chunk_id in IDS
    ]
    bm25 = {
        "chunks": [{"id": chunk_id} for chunk_id in IDS],
        "meta": {
            "chunk_count": 2,
            "term_count": 3,
            "tokenizer": "jieba",
            "k1": 1.5,
            "b": 0.75,
        },
    }
    monkeypatch.setattr(state, "load_active_manifest", lambda: manifest)
    monkeypatch.setattr(state, "corpus_snapshot", lambda _path: {"corpus_sha256": "corpus-hash"})
    monkeypatch.setattr(state, "load_directory", lambda _path: [{"text": "x", "metadata": {}}])
    monkeypatch.setattr(state, "split_records", lambda *args, **kwargs: chunks)
    monkeypatch.setattr(state.vector_store, "get_client", lambda: object())
    monkeypatch.setattr(state.vector_store, "get_collection", lambda *args: object())
    monkeypatch.setattr(state.vector_store, "ids", lambda _collection: list(IDS))
    monkeypatch.setattr(state, "load_index", lambda: bm25)
    monkeypatch.setattr(state, "runtime_metadata", lambda: {"python": "test"})
    return manifest, bm25


def test_verify_project_state_returns_reproducible_identity(verified_state):
    result = state.verify_project_state()
    assert result["index_version"] == "v-test"
    assert result["chunk_count"] == 2
    assert result["bm25"]["term_count"] == 3


def test_corpus_mismatch_aborts_verification(verified_state, monkeypatch):
    monkeypatch.setattr(state, "corpus_snapshot", lambda _path: {"corpus_sha256": "changed"})
    with pytest.raises(state.StateVerificationError, match="语料指纹"):
        state.verify_project_state()


def test_vector_id_mismatch_aborts_verification(verified_state, monkeypatch):
    monkeypatch.setattr(state.vector_store, "ids", lambda _collection: [IDS[0]])
    with pytest.raises(state.StateVerificationError, match="向量索引 chunk ID"):
        state.verify_project_state()


def test_bm25_id_mismatch_aborts_verification(verified_state):
    _, bm25 = verified_state
    bm25["chunks"][1]["id"] = "wrong.md:chunk-0"
    with pytest.raises(state.StateVerificationError, match="BM25 索引 chunk ID"):
        state.verify_project_state()


def test_embedding_model_mismatch_aborts_verification(verified_state):
    manifest, _ = verified_state
    manifest["embedding_model"] = "different-model"
    with pytest.raises(state.StateVerificationError, match="Embedding 模型"):
        state.verify_project_state()
