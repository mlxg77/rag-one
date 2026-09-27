"""配置读取：从 .env 载入 API 与路径配置，供其他模块复用。"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录（config.py 在 src/rag_one/ 下，上跳三级）
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 显式指定项目根的 .env，不依赖"当前工作目录"
load_dotenv(PROJECT_ROOT / ".env")

# ---------- API 配置 ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3-8B")
RERANK_MODEL = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-v2-m3")

# ---------- 路径配置 ----------
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CHROMA_DIR = PROJECT_ROOT / "storage" / "chroma"
BM25_DIR = PROJECT_ROOT / "storage" / "bm25"
MANIFEST_DIR = PROJECT_ROOT / "storage" / "index-manifests"
ACTIVE_INDEX_PATH = PROJECT_ROOT / "storage" / "active-index.json"

# ---------- 索引配置 ----------
COLLECTION_NAME = "rag_mvp_docs"  # v2.0 旧集合名，仅用于迁移现有本地索引
COLLECTION_PREFIX = "rag_docs"     # v2.5 不可变版本集合的前缀
EMBED_BATCH_SIZE = 32             # 每次请求最多向量化多少条文本（chunk）


def require_api_key() -> str:
    """返回 API Key；缺失时给出明确报错（延迟检查，避免 import 时直接崩溃）。"""
    if not OPENAI_API_KEY:
        raise RuntimeError("未找到 OPENAI_API_KEY：请把 .env.example 复制为 .env 并填入硅基流动密钥")
    return OPENAI_API_KEY
