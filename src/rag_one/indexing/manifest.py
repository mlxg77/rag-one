"""不可变索引版本清单与 active pointer 的原子发布。"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from rag_one.config import ACTIVE_INDEX_PATH, COLLECTION_PREFIX, MANIFEST_DIR

SCHEMA_VERSION = 1
REQUIRED_FIELDS = {
    "schema_version",
    "index_version",
    "corpus_sha256",
    "chunk_size",
    "chunk_overlap",
    "chunk_count",
    "chunk_ids_sha256",
    "embedding_model",
    "vector_collection",
    "bm25_file",
    "built_at",
    "git_commit",
}


class ManifestError(RuntimeError):
    """索引版本清单缺失、损坏或与 active pointer 不一致。"""


def _sha256_parts(parts: list[bytes]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(len(part).to_bytes(8, "big"))
        digest.update(part)
    return digest.hexdigest()


def corpus_snapshot(raw_dir: Path) -> dict:
    """计算目录中文件的稳定指纹；文件名和原始字节都参与总哈希。"""
    files: list[dict] = []
    hash_parts: list[bytes] = []
    for path in sorted(p for p in raw_dir.iterdir() if p.is_file()):
        content = path.read_bytes()
        file_hash = hashlib.sha256(content).hexdigest()
        files.append({"name": path.name, "bytes": len(content), "sha256": file_hash})
        hash_parts.extend([path.name.encode("utf-8"), content])
    if not files:
        raise ManifestError(f"语料目录为空：{raw_dir}")
    return {"corpus_sha256": _sha256_parts(hash_parts), "files": files}


def chunk_ids_sha256(chunk_ids: list[str]) -> str:
    """对有序 chunk ID 清单计算稳定哈希。"""
    return _sha256_parts([chunk_id.encode("utf-8") for chunk_id in sorted(chunk_ids)])


def new_index_version(corpus_sha256: str) -> str:
    """生成可读且不会与 Chroma 命名规则冲突的版本号。"""
    # 包含微秒，避免同一秒内的实验构建发生版本冲突。
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{timestamp}-{corpus_sha256[:8]}"


def collection_name(index_version: str) -> str:
    return f"{COLLECTION_PREFIX}__{index_version.replace('-', '_')}"


def manifest_path(index_version: str) -> Path:
    return MANIFEST_DIR / f"{index_version}.json"


def atomic_write_json(path: Path, payload: dict) -> None:
    """先写同目录临时文件，再用 os.replace 原子替换目标。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def validate_manifest(payload: dict) -> dict:
    """验证清单结构并返回副本；不访问索引本体。"""
    if not isinstance(payload, dict):
        raise ManifestError("manifest 顶层必须是 JSON object")
    missing = sorted(REQUIRED_FIELDS - payload.keys())
    if missing:
        raise ManifestError(f"manifest 缺少字段：{', '.join(missing)}")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ManifestError(
            f"不支持的 manifest schema：{payload['schema_version']}（当前 {SCHEMA_VERSION}）"
        )
    if not isinstance(payload["chunk_count"], int) or payload["chunk_count"] < 1:
        raise ManifestError("manifest.chunk_count 必须为正整数")
    if not isinstance(payload["chunk_size"], int) or payload["chunk_size"] < 1:
        raise ManifestError("manifest.chunk_size 必须为正整数")
    if not isinstance(payload["chunk_overlap"], int) or payload["chunk_overlap"] < 0:
        raise ManifestError("manifest.chunk_overlap 必须为非负整数")
    if payload["chunk_overlap"] >= payload["chunk_size"]:
        raise ManifestError("manifest.chunk_overlap 必须小于 chunk_size")
    for field in (
        "index_version",
        "corpus_sha256",
        "chunk_ids_sha256",
        "embedding_model",
        "vector_collection",
        "bm25_file",
        "built_at",
        "git_commit",
    ):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise ManifestError(f"manifest.{field} 必须是非空字符串")
    return dict(payload)


def write_manifest(payload: dict) -> Path:
    """写入不可变版本清单；已存在时拒绝覆盖。"""
    checked = validate_manifest(payload)
    path = manifest_path(checked["index_version"])
    if path.exists():
        raise ManifestError(f"索引版本已存在，拒绝覆盖：{checked['index_version']}")
    atomic_write_json(path, checked)
    return path


def read_manifest(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest 不存在：{path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"manifest 无法读取：{path}：{exc}") from exc
    return validate_manifest(payload)


def activate_manifest(payload: dict) -> None:
    """原子切换 active pointer；失败时旧 pointer 保持不变。"""
    checked = validate_manifest(payload)
    path = manifest_path(checked["index_version"])
    if not path.exists():
        raise ManifestError(f"不能激活未落盘的 manifest：{path}")
    pointer = {
        "schema_version": SCHEMA_VERSION,
        "index_version": checked["index_version"],
        "manifest": path.name,
        "activated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    atomic_write_json(ACTIVE_INDEX_PATH, pointer)


def load_active_manifest() -> dict:
    """读取 active pointer 指向的 manifest，并防止路径逃逸和版本串线。"""
    try:
        pointer = json.loads(ACTIVE_INDEX_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(
            "尚无 active index：请先运行 python -m scripts.rebuild_indexes"
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"active index pointer 无法读取：{exc}") from exc

    if not isinstance(pointer, dict):
        raise ManifestError("active pointer 顶层必须是 JSON object")
    if pointer.get("schema_version") != SCHEMA_VERSION:
        raise ManifestError("active pointer schema_version 不支持")
    name = pointer.get("manifest")
    version = pointer.get("index_version")
    if not isinstance(name, str) or Path(name).name != name:
        raise ManifestError("active pointer 的 manifest 文件名非法")
    path = (MANIFEST_DIR / name).resolve()
    manifest_root = MANIFEST_DIR.resolve()
    if path.parent != manifest_root:
        raise ManifestError("active pointer 指向 manifest 目录之外")
    payload = read_manifest(path)
    if payload["index_version"] != version:
        raise ManifestError("active pointer 与 manifest 的 index_version 不一致")
    return payload


def rollback(index_version: str) -> dict:
    """将已存在的旧版本重新设为 active，不删除任何版本。"""
    payload = read_manifest(manifest_path(index_version))
    activate_manifest(payload)
    return payload
