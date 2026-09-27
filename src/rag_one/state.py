"""项目状态与实验复现信息的只读校验。"""

from __future__ import annotations

import importlib.metadata
import platform
import subprocess
import sys

from rag_one.config import DATA_RAW_DIR, EMBEDDING_MODEL, PROJECT_ROOT
from rag_one.indexing import vector_store
from rag_one.indexing.bm25_store import B, K1, load_index
from rag_one.indexing.manifest import (
    chunk_ids_sha256,
    corpus_snapshot,
    load_active_manifest,
)
from rag_one.ingestion.loaders import load_directory
from rag_one.ingestion.splitter import split_records


class StateVerificationError(RuntimeError):
    """当前语料、双索引和 active manifest 不一致。"""


def _git_info() -> dict:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        return {"commit": commit, "dirty": bool(status)}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": "unknown", "dirty": None}


def runtime_metadata() -> dict:
    packages = {}
    for name in ("chromadb", "jieba", "openai", "httpx", "pymupdf", "streamlit"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": packages,
        "git": _git_info(),
    }


def verify_project_state() -> dict:
    """严格验证语料、切分、向量和 BM25 全部属于 active version。"""
    manifest = load_active_manifest()
    if manifest["embedding_model"] != EMBEDDING_MODEL:
        raise StateVerificationError("当前 Embedding 模型与 active manifest 不一致")
    snapshot = corpus_snapshot(DATA_RAW_DIR)
    if snapshot["corpus_sha256"] != manifest["corpus_sha256"]:
        raise StateVerificationError("当前语料指纹与 active manifest 不一致")

    records = load_directory(DATA_RAW_DIR)
    chunks = split_records(
        records,
        chunk_size=manifest["chunk_size"],
        chunk_overlap=manifest["chunk_overlap"],
    )
    source_ids = [chunk["id"] for chunk in chunks]
    source_hash = chunk_ids_sha256(source_ids)
    if source_hash != manifest["chunk_ids_sha256"]:
        raise StateVerificationError("当前切分 chunk ID 与 active manifest 不一致")
    if len(source_ids) != manifest["chunk_count"]:
        raise StateVerificationError("当前切分 chunk 数与 active manifest 不一致")

    client = vector_store.get_client()
    collection = vector_store.get_collection(client, manifest["vector_collection"])
    vector_ids = vector_store.ids(collection)
    if chunk_ids_sha256(vector_ids) != source_hash or len(vector_ids) != len(source_ids):
        raise StateVerificationError("向量索引 chunk ID 与当前切分不一致")

    bm25 = load_index()
    bm25_ids = [chunk["id"] for chunk in bm25["chunks"]]
    if chunk_ids_sha256(bm25_ids) != source_hash or len(bm25_ids) != len(source_ids):
        raise StateVerificationError("BM25 索引 chunk ID 与当前切分不一致")
    if bm25["meta"].get("chunk_count") != len(source_ids):
        raise StateVerificationError("BM25 索引条数元数据与当前切分不一致")

    return {
        "index_version": manifest["index_version"],
        "corpus_sha256": manifest["corpus_sha256"],
        "chunk_ids_sha256": source_hash,
        "chunk_size": manifest["chunk_size"],
        "chunk_overlap": manifest["chunk_overlap"],
        "chunk_count": len(source_ids),
        "vector_collection": manifest["vector_collection"],
        "bm25_file": manifest["bm25_file"],
        "embedding_model": manifest["embedding_model"],
        "bm25": {
            "tokenizer": bm25["meta"].get("tokenizer"),
            "k1": bm25["meta"].get("k1", K1),
            "b": bm25["meta"].get("b", B),
            "term_count": bm25["meta"]["term_count"],
        },
        "runtime": runtime_metadata(),
    }
