"""将向量与 BM25 构建为同一不可变版本，再原子发布 active pointer。"""

from __future__ import annotations

import hashlib
import subprocess
import time
from pathlib import Path

from rag_one.config import BM25_DIR, DATA_RAW_DIR, EMBEDDING_MODEL, PROJECT_ROOT
from rag_one.indexing import vector_store
from rag_one.indexing.bm25_store import build_index as build_bm25_index
from rag_one.indexing.bm25_store import clear_index_cache, load_index as load_bm25_index, save_index
from rag_one.indexing.embeddings import embed_texts
from rag_one.indexing.manifest import (
    SCHEMA_VERSION,
    activate_manifest,
    chunk_ids_sha256,
    collection_name,
    corpus_snapshot,
    manifest_path,
    new_index_version,
    write_manifest,
)
from rag_one.ingestion.loaders import load_directory
from rag_one.ingestion.splitter import CHUNK_OVERLAP, CHUNK_SIZE, split_records


class IndexBuildError(RuntimeError):
    """双索引构建或发布校验失败。"""


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def _validate_ids(expected: list[str], actual: list[str], label: str) -> None:
    if set(actual) != set(expected) or len(actual) != len(expected):
        missing = sorted(set(expected) - set(actual))[:5]
        extra = sorted(set(actual) - set(expected))[:5]
        raise IndexBuildError(
            f"{label} chunk ID 不一致：expected={len(expected)} actual={len(actual)} "
            f"missing={missing} extra={extra}"
        )


def build_and_publish_indexes(
    raw_dir: Path = DATA_RAW_DIR,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> dict:
    """构建双索引、完成交叉校验并原子发布；旧 active version 始终保留。"""
    if chunk_size < 1 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk 参数非法：要求 chunk_size > chunk_overlap >= 0")

    build_start = time.perf_counter()
    snapshot = corpus_snapshot(raw_dir)
    records = load_directory(raw_dir)
    chunks = split_records(records, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        raise IndexBuildError(f"没有从 {raw_dir} 加载到任何 chunk")

    chunk_ids = [chunk["id"] for chunk in chunks]
    if len(chunk_ids) != len(set(chunk_ids)):
        raise IndexBuildError("切分结果含重复 chunk ID")

    index_version = new_index_version(snapshot["corpus_sha256"])
    vector_name = collection_name(index_version)
    bm25_path = BM25_DIR / f"{index_version}.json"
    client = vector_store.get_client()
    collection_created = False
    bm25_written = False
    manifest_written = False

    try:
        embeddings = embed_texts([chunk["text"] for chunk in chunks])
        if len(embeddings) != len(chunks):
            raise IndexBuildError(
                f"Embedding 数量不一致：{len(embeddings)} != {len(chunks)}"
            )

        collection = vector_store.create_collection(client, vector_name)
        collection_created = True
        metadatas = [
            {**chunk["metadata"], "content_hash": _content_hash(chunk["text"])}
            for chunk in chunks
        ]
        vector_store.upsert_chunks(
            collection,
            ids=chunk_ids,
            texts=[chunk["text"] for chunk in chunks],
            metadatas=metadatas,
            embeddings=embeddings,
        )
        if vector_store.count(collection) != len(chunks):
            raise IndexBuildError("向量集合条数校验失败")
        _validate_ids(chunk_ids, vector_store.ids(collection), "向量索引")
        probe = collection.query(
            query_embeddings=[embeddings[0]],
            n_results=1,
            include=["metadatas"],
        )
        if not probe["ids"][0]:
            raise IndexBuildError("向量集合可查询性探针失败")

        bm25 = build_bm25_index(chunks)
        save_index(bm25, bm25_path)
        bm25_written = True
        persisted_bm25 = load_bm25_index(bm25_path)
        bm25_ids = [chunk["id"] for chunk in persisted_bm25["chunks"]]
        _validate_ids(chunk_ids, bm25_ids, "BM25 索引")
        build_duration_ms = round((time.perf_counter() - build_start) * 1000)

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "index_version": index_version,
            "corpus_sha256": snapshot["corpus_sha256"],
            "corpus_files": snapshot["files"],
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "chunk_count": len(chunks),
            "chunk_ids_sha256": chunk_ids_sha256(chunk_ids),
            "embedding_model": EMBEDDING_MODEL,
            "vector_collection": vector_name,
            "bm25_file": _relative(bm25_path),
            "built_at": bm25["meta"]["built_at"],
            "git_commit": _git_commit(),
            "build_duration_ms": build_duration_ms,
        }
        write_manifest(manifest)
        manifest_written = True

        # 唯一发布点：此前所有产物均使用不可变版本名，失败不会影响旧 pointer。
        activate_manifest(manifest)
        clear_index_cache()
        return {
            "index_version": index_version,
            "docs": len({record["metadata"]["source"] for record in records}),
            "chunks": len(chunks),
            "collection_count": vector_store.count(collection),
            "bm25_terms": bm25["meta"]["term_count"],
            "build_duration_ms": build_duration_ms,
            "publish_duration_ms": round((time.perf_counter() - build_start) * 1000),
            "manifest": _relative(manifest_path(index_version)),
        }
    except Exception:
        # 完整 manifest 已写出但 pointer 切换失败时保留候选版本，便于诊断或手工激活。
        if not manifest_written:
            if collection_created:
                vector_store.delete_collection(client, vector_name)
            if bm25_written and bm25_path.exists():
                bm25_path.unlink()
        raise
