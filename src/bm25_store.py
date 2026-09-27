"""BM25 关键词检索：中文分词 → 倒排索引 → BM25 打分。

链路：chunk 原文 → jieba 分词 → 建库（storage/bm25/index.json）
      → 问题分词 → BM25 Top-N。

持久化的是「可重建数据」（原文 + 分词结果 + 倒排表），不是 pickle 序列化的
内存对象：结构透明、可跨版本读取，加载后即可复算全部统计量。
"""

import json
import math
import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import jieba

from src.config import BM25_DIR

INDEX_PATH = BM25_DIR / "index.json"

# 第一版使用经典稳定默认值；后续单变量实验只改传参，不需要重建索引
K1 = 1.5   # 词频饱和参数
B = 0.75   # 长度归一化强度（0 = 不归一化，1 = 完全归一化）


def tokenize(text: str) -> list[str]:
    """jieba 精确分词：去空白、丢纯标点、英文小写化。"""
    tokens: list[str] = []
    for piece in jieba.lcut(text):
        piece = piece.strip().lower()
        if piece and any(ch.isalnum() for ch in piece):
            tokens.append(piece)
    return tokens


def build_index(chunks: list[dict]) -> dict:
    """从切分结果构建 BM25 索引（纯函数：不读盘、不写盘，方便测试）。

    chunks：split_records() 的输出，每项含 id / text / metadata(source, page?)。
    返回内存索引：chunks（补分词与统计所需字段）+ postings 倒排表 + avgdl。
    """
    prepared: list[dict] = []
    postings: dict[str, list[list[int]]] = {}  # 词 -> [[chunk 下标, 词频], ...]
    total_len = 0

    for idx, chunk in enumerate(chunks):
        tokens = tokenize(chunk["text"])
        prepared.append(
            {
                "id": chunk["id"],
                "source": chunk["metadata"].get("source"),
                "page": chunk["metadata"].get("page"),
                "text": chunk["text"],
                "tokens": tokens,
            }
        )
        total_len += len(tokens)

        tf: dict[str, int] = {}
        for tok in tokens:
            tf[tok] = tf.get(tok, 0) + 1
        for tok, count in tf.items():
            postings.setdefault(tok, []).append([idx, count])

    return {
        "meta": {
            "built_at": datetime.now().isoformat(timespec="seconds"),
            "tokenizer": "jieba",
            "chunk_count": len(prepared),
            "term_count": len(postings),
        },
        "chunks": prepared,
        "postings": postings,
        "avgdl": total_len / len(prepared) if prepared else 0.0,
    }


def save_index(index: dict, path: Path = INDEX_PATH) -> None:
    """全量写出索引：先写 .tmp 再原子替换（写一半失败不破坏旧索引）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    os.replace(tmp, path)  # 同目录原子替换：磁盘上只会是"旧版或完整新版"，无半截文件


@lru_cache(maxsize=1)
def load_index(path: str = str(INDEX_PATH)) -> dict:
    """加载索引（进程内缓存一次：评估 32 题不重复解析同一个 JSON）。"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"BM25 索引不存在：{p}（先运行 python -X utf8 ingest_bm25.py）")
    return json.loads(p.read_text(encoding="utf-8"))


def _idf(df: int, n: int) -> float:
    """Lucene 变体 IDF：ln(1 + (N - df + 0.5)/(df + 0.5))，恒为正、无负分。"""
    return math.log(1 + (n - df + 0.5) / (df + 0.5))


def score_query(query_tokens: list[str], index: dict, k1: float = K1, b: float = B) -> dict[int, float]:
    """对含查询词的 chunk 计算 BM25 总分，返回 {chunk 下标: 分数}。

    只遍历查询词的 postings（倒排的意义：不扫全库）；
    查询词去重——同一词在问题里出现多次只贡献一次。
    """
    n = len(index["chunks"])
    avgdl = index["avgdl"]
    scores: dict[int, float] = {}

    for term in sorted(set(query_tokens)):
        postings = index["postings"].get(term)
        if not postings:
            continue
        idf = _idf(len(postings), n)
        for idx, tf in postings:
            dl = len(index["chunks"][idx]["tokens"])
            denom = tf + k1 * (1 - b + b * dl / avgdl)
            scores[idx] = scores.get(idx, 0.0) + idf * tf * (k1 + 1) / denom

    return scores


def search(
    question: str,
    top_k: int = 10,
    index: dict | None = None,
    k1: float = K1,
    b: float = B,
) -> list[dict]:
    """BM25 Top-K 检索，返回结构与 retriever.retrieve() 对齐：

    [{rank, id, score, source, page, text}, ...]，按分数降序、同分按 id 升序兜底。
    """
    if top_k < 1:
        raise ValueError(f"top_k 必须 >= 1，收到 {top_k}")

    idx = index if index is not None else load_index()

    query_tokens = tokenize(question)
    if not query_tokens:
        return []

    scores = score_query(query_tokens, idx, k1=k1, b=b)
    if not scores:
        return []

    ranked = sorted(
        scores.items(),
        key=lambda item: (-item[1], idx["chunks"][item[0]]["id"]),
    )[:top_k]

    hits: list[dict] = []
    for rank, (chunk_idx, score) in enumerate(ranked, start=1):
        chunk = idx["chunks"][chunk_idx]
        hits.append(
            {
                "rank": rank,
                "id": chunk["id"],
                "score": score,
                "source": chunk["source"],
                "page": chunk["page"],
                "text": chunk["text"],
            }
        )
    return hits


if __name__ == "__main__":
    from src.retriever import format_hits  # 两路检索结果结构一致，复用同一排版函数

    demo_questions = [
        "普通员工去上海出差，酒店每晚含税最高可以报销多少？",  # 与 retriever.py 演示同题，便于两路对照
        "报销必须在多少天内提交",
    ]
    for question in demo_questions:
        print(format_hits(question, search(question, top_k=5)))
        print("=" * 60)