"""配置读取：从 .env 载入 API 与路径配置，供其他模块复用。"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录（config.py 在 src/ 下，上跳两级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 显式指定项目根的 .env，不依赖"当前工作目录"
load_dotenv(PROJECT_ROOT / ".env")

# ---------- API 配置 ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3-8B")

# ---------- 路径配置 ----------
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CHROMA_DIR = PROJECT_ROOT / "storage" / "chroma"

# ---------- 索引配置 ----------
COLLECTION_NAME = "rag_mvp_docs"  # Chroma 集合名：3~512 字符，只含字母/数字/._-，首尾必须是字母或数字
EMBED_BATCH_SIZE = 32             # 每次请求最多向量化多少条文本（chunk）


def require_api_key() -> str:
    """返回 API Key；缺失时给出明确报错（延迟检查，避免 import 时直接崩溃）。"""
    if not OPENAI_API_KEY:
        raise RuntimeError("未找到 OPENAI_API_KEY：请把 .env.example 复制为 .env 并填入硅基流动密钥")
    return OPENAI_API_KEY