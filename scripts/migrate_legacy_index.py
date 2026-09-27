"""将本机 v2.0 固定名称索引登记为首个 v2.5 active version，不重新调用 API。"""

import subprocess

from rag_one.config import (
    COLLECTION_NAME,
    DATA_RAW_DIR,
    EMBEDDING_MODEL,
    PROJECT_ROOT,
)
from rag_one.indexing import vector_store
from rag_one.indexing.bm25_store import INDEX_PATH, load_index
from rag_one.indexing.manifest import (
    SCHEMA_VERSION,
    activate_manifest,
    chunk_ids_sha256,
    corpus_snapshot,
    manifest_path,
    write_manifest,
)
from rag_one.ingestion.loaders import load_directory
from rag_one.ingestion.splitter import CHUNK_OVERLAP, CHUNK_SIZE, split_records


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> None:
    snapshot = corpus_snapshot(DATA_RAW_DIR)
    chunks = split_records(load_directory(DATA_RAW_DIR))
    ids = [chunk["id"] for chunk in chunks]

    client = vector_store.get_client()
    collection = vector_store.get_collection(client, COLLECTION_NAME)
    vector_ids = vector_store.ids(collection)
    bm25 = load_index(INDEX_PATH)
    bm25_ids = [chunk["id"] for chunk in bm25["chunks"]]
    if set(ids) != set(vector_ids) or set(ids) != set(bm25_ids):
        raise RuntimeError("旧向量索引、BM25 与当前切分不一致，不能迁移；请重建")

    version = f"legacy-v2-{snapshot['corpus_sha256'][:8]}"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "index_version": version,
        "corpus_sha256": snapshot["corpus_sha256"],
        "corpus_files": snapshot["files"],
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "chunk_count": len(ids),
        "chunk_ids_sha256": chunk_ids_sha256(ids),
        "embedding_model": EMBEDDING_MODEL,
        "vector_collection": COLLECTION_NAME,
        "bm25_file": INDEX_PATH.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix(),
        "built_at": bm25["meta"]["built_at"],
        "git_commit": _git_commit(),
    }
    path = manifest_path(version)
    if not path.exists():
        write_manifest(payload)
    activate_manifest(payload)
    print(f"已激活旧索引版本：{version}")


if __name__ == "__main__":
    main()
