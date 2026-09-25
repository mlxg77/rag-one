"""RAG 主流程：把检索与生成串成一条链；命令行问答入口。"""

from src.generator import generate_answer
from src.retriever import DEFAULT_TOP_K, format_hits, retrieve


def ask(question: str, top_k: int = DEFAULT_TOP_K) -> dict:
    """完整 RAG 一问：检索 -> 生成；检索结果与答案分开返回。"""
    hits = retrieve(question, top_k=top_k)
    result = generate_answer(question, hits)
    return {
        "question": question,
        "hits": hits,           # 供单独查看 / 核对引用
        "answer": result["answer"],
        "usage": result["usage"],
    }

if __name__ == "__main__":
    print("RAG 问答（输入 q 退出）")
    while True:
        question = input("\n问题> ").strip()
        if not question:
            continue
        if question.lower() in {"q", "quit", "exit"}:
            break

        result = ask(question)

        print("\n---- 检索结果 ----")
        print(format_hits(result["question"], result["hits"]))

        print("---- 回答 ----")
        print(result["answer"])

        usage = result["usage"]
        print(f'\n(tokens: prompt={usage["prompt_tokens"]}, completion={usage["completion_tokens"]})')