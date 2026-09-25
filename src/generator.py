"""答案生成：把检索结果组装成 Prompt，调用 LLM 生成带引用的回答。"""

from openai import OpenAI

from src.config import LLM_MODEL, OPENAI_BASE_URL, require_api_key

LLM_TEMPERATURE = 0.2  # 低随机性：制度问答要稳定、便于评估复现

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """懒加载 LLM 客户端（与 embeddings.py 同模式）。"""
    global _client
    if _client is None:
        _client = OpenAI(api_key=require_api_key(), base_url=OPENAI_BASE_URL)
    return _client

PROMPT_TEMPLATE = """你是一个文档问答助手。

请只根据"参考资料"回答问题。
如果参考资料不足以支持答案，请明确回答"根据现有资料无法确定"。
不要使用参考资料之外的事实。
回答后列出使用的资料编号。

参考资料：
{context}

问题：
{question}"""

def build_prompt(question: str, hits: list[dict]) -> str:
    """把检索结果组装成第一版 Prompt（编号 [1]..[K] 与 hits 的 rank 对应）。"""
    blocks: list[str] = []
    for hit in hits:
        page = hit["page"]
        location = hit["source"] if page is None else f'{hit["source"]}，第 {page} 页'
        blocks.append(f'[{hit["rank"]}] 来源：{location}\n内容：{hit["text"]}')
    context = "\n\n".join(blocks)
    return PROMPT_TEMPLATE.format(context=context, question=question)

def generate_answer(question: str, hits: list[dict]) -> dict:
    """调用 LLM 生成答案，返回 {answer, usage}。"""
    prompt = build_prompt(question, hits)
    resp = _get_client().chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=LLM_TEMPERATURE,
        extra_body={"enable_thinking": False},  # Qwen3 关闭思考：快 30 倍、省 token
    )
    return {
        "answer": resp.choices[0].message.content.strip(),
        "usage": {
            "prompt_tokens": resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
        },
    }