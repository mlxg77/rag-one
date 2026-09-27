"""生成模块单元测试：Prompt 结构 / 调用参数 / 返回组装（LLM 全替身，离线）。

运行：python -X utf8 -m pytest tests/test_generator.py -v
"""

from types import SimpleNamespace

from src import generator
from src.config import LLM_MODEL
from src.generator import LLM_TEMPERATURE, build_prompt, generate_answer


def make_hits() -> list[dict]:
    return [
        {"rank": 1, "id": "a.md:chunk-0", "score": 0.9, "source": "a.md", "page": None, "text": "内容一"},
        {
            "rank": 2,
            "id": "10-faq.pdf:page-3:chunk-0",
            "score": 0.8,
            "source": "10-faq.pdf",
            "page": 3,
            "text": "内容二",
        },
    ]


def test_build_prompt_structure():
    prompt = build_prompt("怎么报销？", make_hits())
    assert "无法确定" in prompt                       # 拒答指令
    assert "[1] 来源：a.md" in prompt
    assert "[2] 来源：10-faq.pdf，第 3 页" in prompt  # PDF 带页码
    assert "内容一" in prompt and "内容二" in prompt
    assert prompt.rstrip().endswith("怎么报销？")      # 问题在结尾


def test_build_prompt_uses_hit_rank():
    hits = [{"rank": 7, "id": "x", "score": 0.5, "source": "x.md", "page": None, "text": "T"}]
    assert "[7] 来源：x.md" in build_prompt("Q", hits)


class FakeCompletions:
    """替身：记录调用参数，返回固定响应。"""

    def __init__(self):
        self.kwargs: dict | None = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="  答案带空白  "))],
            usage=SimpleNamespace(prompt_tokens=123, completion_tokens=45),
        )


def test_generate_answer_params_and_strip(monkeypatch):
    completions = FakeCompletions()
    monkeypatch.setattr(generator, "_client", SimpleNamespace(chat=SimpleNamespace(completions=completions)))

    out = generate_answer("怎么报销？", make_hits())

    kwargs = completions.kwargs
    assert kwargs["model"] == LLM_MODEL
    assert kwargs["temperature"] == LLM_TEMPERATURE                    # 0.2：稳定可复现
    assert kwargs["extra_body"] == {"enable_thinking": False}          # Qwen3 关闭思考
    assert kwargs["messages"] == [{"role": "user", "content": build_prompt("怎么报销？", make_hits())}]
    assert out == {
        "answer": "答案带空白",                                        # strip 生效
        "usage": {"prompt_tokens": 123, "completion_tokens": 45},
    }
