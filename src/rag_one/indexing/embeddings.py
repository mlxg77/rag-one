"""Embedding 调用：把文本批量转成向量（硅基流动，OpenAI 兼容接口）。"""

from openai import OpenAI

from rag_one.config import EMBED_BATCH_SIZE, EMBEDDING_MODEL, OPENAI_BASE_URL, require_api_key

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """懒加载客户端：避免 import 本模块时就要求密钥存在。"""
    global _client
    if _client is None:
        _client = OpenAI(api_key=require_api_key(), base_url=OPENAI_BASE_URL)
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量向量化，返回顺序与输入一一对应。"""
    if not texts:
        return []

    client = _get_client()
    vectors: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        resp = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        # 对齐顺序：按返回的 index 排序后再取 embedding
        vectors.extend(item.embedding for item in sorted(resp.data, key=lambda d: d.index))
    return vectors


def embed_query(text: str) -> list[float]:
    """单条文本向量化（阶段五检索查询时使用）。"""
    return embed_texts([text])[0]
