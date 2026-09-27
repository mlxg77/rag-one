"""相似度检索：把问题向量化，在 ChromaDB 里取 Top-K 相关 chunk。"""

from rag_one.indexing import vector_store
from rag_one.indexing.embeddings import embed_query

DEFAULT_TOP_K = 5  # 默认返回条数（调用方可通过参数覆盖）

def retrieve(question: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """检索与问题最相关的 top_k 个 chunk，按相关度从高到低返回。"""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question 不能为空")
    if top_k < 1:
        raise ValueError(f"top_k 必须 >= 1，收到 {top_k}")
    # 1) 问题向量化：必须与建索引时同一个模型（bge-m3），坐标系才一致
    query_vector = embed_query(question)

    # 2) 打开已建好的集合（与 indexer.py 用的是同一套函数，纯读）
    client = vector_store.get_client()
    collection = vector_store.get_collection(client)

    # 3) 查询：query_embeddings 收"查询向量列表"（支持一次查多个问题）
    result = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    # 打印结果 result
    # print("--result",result)

    # 4) 解包嵌套列表：外层 [0] 表示"第 1 个查询"的结果
    ids = result["ids"][0]
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    # 5) 组装为统一结构，rank 从 1 开始
    hits: list[dict] = []
    for rank, (chunk_id, text, meta, distance) in enumerate(
        zip(ids, documents, metadatas, distances), start=1
    ):
        hits.append(
            {
                "rank": rank,
                "id": chunk_id,
                "score": 1 - distance,   # 余弦相似度 = 1 - 余弦距离
                "distance": distance,    # 保留原始距离，调试用
                "source": meta.get("source"),
                "page": meta.get("page"),      # 仅 PDF 有；md 返回 None
                "text": text,                  # 完整 chunk 原文
            }
        )
    return hits

def format_hits(question: str, hits: list[dict]) -> str:
    """把检索结果排版成可读文本（终端演示与调试用）。"""
    if not hits:
        return f"问题：{question}\n（未检索到任何结果：索引为空或尚未建立）"

    lines = [f"问题：{question}", ""]
    for hit in hits:
        page = hit["page"]
        location = hit["source"] if page is None else f'{hit["source"]} 第 {page} 页'
        lines.append(f'Rank {hit["rank"]} | score={hit["score"]:.4f} | {location}')
        lines.append(f'  chunk: {hit["id"]}')
        lines.append(f'  内容: {hit["text"]}')
        lines.append("")
    return "\n".join(lines)

if __name__ == "__main__":
    demo_questions = [
        "普通员工去上海出差，酒店每晚含税最高可以报销多少？",  # 1. 评估集原文
        "出差住酒店一晚最多能报多少钱",                        # 2. 同义改写（换措辞）
        "公司食堂每天几点开饭？",                              # 3. 库外问题（知识库没有）
    ]
    for question in demo_questions:
        hits = retrieve(question)
        print(format_hits(question, hits))
        print("=" * 60)
