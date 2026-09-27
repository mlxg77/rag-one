"""Reranker：对候选做交叉编码（cross-encoder）精排，走硅基流动 Rerank API。

双塔召回（向量 / BM25）负责「找得全」——query 与 doc 分开编码，快；
交叉编码重排负责「排得准」——query+doc 拼对进模型打分，慢但准。
所以链路是「召回宽（Top-20）→ 重排窄（Top-K）」，重排只处理小候选集。

接口与供应商无关：rerank(question, candidates, top_k)——换模型 / 供应商只改本模块。
"""

import math

import httpx

from rag_one.config import OPENAI_BASE_URL, RERANK_MODEL, require_api_key

RERANK_TIMEOUT = 30  # 单次重排请求超时（秒）

_last_usage: dict = {}  # 最近一次调用上报的用量（含 tokens），供演示观察成本


class RerankError(RuntimeError):
    """Reranker 调用失败（网络错误 / 接口报错 / 响应缺字段）。"""


def last_usage() -> dict:
    """最近一次 rerank 调用上报的 meta（token 等）；无记录时为空 dict。"""
    return dict(_last_usage)


def _call_rerank_api(question: str, texts: list[str]) -> list[float]:
    """调 Rerank API 给每个候选打分，返回按输入顺序对齐的分数列表。

    失败一律抛 RerankError（本模块不吞错，回退策略由调用方决定）。
    """
    global _last_usage
    _last_usage = {}
    url = OPENAI_BASE_URL.rstrip("/") + "/rerank"
    payload = {
        "model": RERANK_MODEL,
        "query": question,
        "documents": texts,
        "top_n": len(texts),        # 拿全部候选的分数，排序与截断由本模块控制
        "return_documents": False,  # 不用把原文传回来，我们手里有
    }
    try:
        resp = httpx.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {require_api_key()}"},
            timeout=RERANK_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as exc:
        raise RerankError(f"Rerank API 请求失败：{exc}") from exc
    except ValueError as exc:  # 响应不是合法 JSON
        raise RerankError(f"Rerank API 响应无法解析：{exc}") from exc

    if not isinstance(data, dict):
        raise RerankError("Rerank API 响应顶层必须是 JSON object")
    results = data.get("results")
    if not isinstance(results, list) or not results:
        raise RerankError(f"Rerank API 响应缺少 results：{data}")

    if len(results) != len(texts):
        raise RerankError(
            f"Rerank API 返回数量不完整：{len(results)} != {len(texts)}"
        )
    scores: list[float | None] = [None] * len(texts)
    for item in results:
        if not isinstance(item, dict):
            raise RerankError("Rerank API results 中存在非 object 项")
        index = item.get("index")
        score = item.get("relevance_score")
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(texts):
            raise RerankError(f"Rerank API 返回非法 index：{index}")
        if scores[index] is not None:
            raise RerankError(f"Rerank API 返回重复 index：{index}")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not math.isfinite(score):
            raise RerankError(f"Rerank API 返回非法 relevance_score：{score}")
        scores[index] = float(score)
    if any(score is None for score in scores):
        raise RerankError("Rerank API 未返回全部候选的分数")
    _last_usage = data.get("meta", {})
    return [float(score) for score in scores]


def rerank(question: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """交叉编码重排：返回按重排分降序的 top_k 个候选（保留全部原字段）。

    - 候选须含 text（发给重排模型的正文）；
    - 输出每条新增 rerank_score，rank 重写为最终名次（1 起）——
      重排前名次请调用方提前另存（混合链路记到 rrf_rank）；
    - 空候选直接返回 []（实测 Rerank API 不接受空列表，会 400）；
    - API 失败抛 RerankError，不修改传入的候选（副本上操作）。
    """
    if not candidates:
        return []
    if top_k < 1:
        raise ValueError(f"top_k 必须 >= 1，收到 {top_k}")

    scores = _call_rerank_api(question, [c["text"] for c in candidates])

    scored = [dict(c, rerank_score=s) for c, s in zip(candidates, scores)]
    # 分数降序；同分保持输入顺序（sorted 稳定），不在平局时乱动上游共识序
    ranked = sorted(scored, key=lambda e: -e["rerank_score"])[:top_k]

    results: list[dict] = []
    for rank, entry in enumerate(ranked, start=1):
        entry["rank"] = rank
        results.append(entry)
    return results


if __name__ == "__main__":
    # 演示：三条候选（第二条才是真正相关的），看重排把它抬到第一
    demo_question = "普通员工去上海出差，酒店每晚含税最高可以报销多少？"
    demo_candidates = [
        {
            "id": "demo:chunk-0", "source": "10-faq.md", "page": None,
            "text": "公司提供免费咖啡和茶水间。",
            "score": 0.030, "rank": 1, "vector_rank": 1, "bm25_rank": 3,
        },
        {
            "id": "demo:chunk-1", "source": "06-travel-policy.md", "page": None,
            "text": "员工出差住宿费标准：上海等一线城市每晚含税不超过 600 元。",
            "score": 0.028, "rank": 2, "vector_rank": 4, "bm25_rank": 1,
        },
        {
            "id": "demo:chunk-2", "source": "09-it-support.md", "page": None,
            "text": "IT 报修请提交工单，一般一个工作日内响应。",
            "score": 0.026, "rank": 3, "vector_rank": 3, "bm25_rank": 5,
        },
    ]
    for hit in rerank(demo_question, demo_candidates, top_k=3):
        print(f'Rank {hit["rank"]} | rerank={hit["rerank_score"]:.4f} | {hit["id"]}')
    print(f"本次调用用量：{last_usage().get('tokens', {})}")
