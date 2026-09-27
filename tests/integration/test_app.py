"""Streamlit 界面测试：渲染 / 模式切换 / 提问展示 / 索引重建。全部替身，离线。

AppTest 每次 run 会重新执行 app.py 脚本；脚本里的 from-import 取的是模块
当前属性，因此 monkeypatch 提供方模块（rag_one.pipeline / rag_one.indexing.indexer）
即可生效，且不触网、不碰真实 API Key。

运行：python -X utf8 -m pytest tests/integration/test_app.py -v
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

import rag_one.indexing.indexer
import rag_one.pipeline

APP_PATH = Path(__file__).resolve().parents[2] / "app.py"


def make_candidates() -> list[dict]:
    return [
        {
            "rank": 1, "id": "a.md:chunk-0", "score": 0.9, "source": "a.md", "page": None,
            "text": "候选一文本", "vector_rank": 1, "bm25_rank": None, "rrf_rank": 1,
            "rerank_score": 0.88, "final_rank": 1,
        },
        {
            "rank": 2, "id": "b.md:chunk-0", "score": 0.8, "source": "b.md", "page": 2,
            "text": "候选二文本", "vector_rank": 3, "bm25_rank": 2, "rrf_rank": 2,
            "rerank_score": 0.77, "final_rank": 2,
        },
    ]


def make_result() -> dict:
    return {
        "question": "测试问题", "mode": "hybrid_rerank", "settings": {},
        "stages": [
            {"name": "向量召回", "elapsed_ms": 12.3, "count": 20},
            {"name": "答案生成", "elapsed_ms": 2500.0, "count": 2},
        ],
        "total_ms": 2512.3,
        "candidates": make_candidates(),
        "hits": make_candidates(),
        "answer": "这是测试回答。[1]",
        "usage": {"prompt_tokens": 100, "completion_tokens": 20},
        "rerank_tokens": 55,
        "warnings": ["演示警告"],
    }


def run_app() -> AppTest:
    at = AppTest.from_file(str(APP_PATH), default_timeout=60)
    at.run()
    return at


def click_button(at: AppTest, label: str) -> AppTest:
    labels = [b.label for b in at.button]
    at.button[labels.index(label)].click().run()
    return at


# ---------------- 渲染与模式切换 ----------------


def test_render_basics():
    at = run_app()
    assert not at.exception
    assert any("rag-one" in t.value for t in at.title)
    assert "提问" in [b.label for b in at.button]

    assert len(at.selectbox) == 1
    assert at.selectbox[0].label == "检索模式"
    assert len(at.selectbox[0].options) == 4  # 四种链路

    assert len(at.slider) == 2  # 默认混合重排：Top-K + 候选数
    assert at.slider[0].label.startswith("最终 Top-K")
    assert len(at.info) >= 1  # 未提问时的引导提示


def test_mode_switch_controls_candidate_slider():
    at = run_app()
    at.selectbox[0].set_value("BM25 关键词（仅关键词）").run()
    assert len(at.slider) == 1  # 单路模式不显示候选数

    at.selectbox[0].set_value("混合检索（两路召回 + RRF 融合）").run()
    assert len(at.slider) == 2


# ---------------- 提问路径 ----------------


def test_ask_flow_renders_answer_candidates_and_refs(monkeypatch):
    calls: dict = {}

    def fake_run_chain(mode, question, **kwargs):
        calls["mode"] = mode
        calls["question"] = question
        calls.update(kwargs)
        return make_result()

    monkeypatch.setattr(rag_one.pipeline, "run_chain", fake_run_chain)

    at = run_app()
    at.text_input[0].set_value("测试问题").run()
    click_button(at, "提问")

    assert not at.exception
    # 界面默认参数原样透传给 pipeline
    assert calls["mode"] == "hybrid_rerank"
    assert calls["question"] == "测试问题"
    assert calls["top_k"] == 5
    assert calls["candidate_k"] == 20

    assert any(m.value == "这是测试回答。[1]" for m in at.markdown)
    assert any("分阶段耗时" in m.value for m in at.markdown)

    assert len(at.dataframe) == 1
    df = at.dataframe[0].value
    assert len(df) == 2  # 候选池两行
    assert set(df.columns) >= {"来源", "向量#", "BM25#", "融合#", "重排分", "最终#", "片段"}

    assert len(at.expander) == 2  # 最终引用两条
    assert any("rerank=55" in c.value for c in at.caption)
    assert [w.value for w in at.warning] == ["演示警告"]


def test_ask_empty_question_warns():
    at = run_app()
    click_button(at, "提问")
    assert not at.exception
    assert any("请先输入问题" in w.value for w in at.warning)
    assert len(at.dataframe) == 0  # 未产生结果


def test_ask_failure_shows_error_and_page_survives(monkeypatch):
    def boom(mode, question, **kwargs):
        raise RuntimeError("模拟失败")

    monkeypatch.setattr(rag_one.pipeline, "run_chain", boom)

    at = run_app()
    at.text_input[0].set_value("问题").run()
    click_button(at, "提问")
    assert not at.exception
    assert any("问答失败" in e.value and "模拟失败" in e.value for e in at.error)


def test_ask_missing_bm25_index_gives_hint(monkeypatch):
    def missing(mode, question, **kwargs):
        raise FileNotFoundError("index.json")

    monkeypatch.setattr(rag_one.pipeline, "run_chain", missing)

    at = run_app()
    at.text_input[0].set_value("问题").run()
    click_button(at, "提问")
    assert any("BM25 索引不存在" in e.value for e in at.error)


# ---------------- 索引重建路径 ----------------


def test_rebuild_success_both_indexes(monkeypatch):
    calls: list[str] = []

    def fake_rebuild():
        calls.append("both")
        return {
            "index_version": "v-test",
            "docs": 10,
            "chunks": 111,
            "collection_count": 111,
            "bm25_terms": 1515,
        }

    monkeypatch.setattr(rag_one.indexing.indexer, "build_and_publish_indexes", fake_rebuild)

    at = run_app()
    click_button(at, "重建索引")

    assert not at.exception
    assert calls == ["both"]
    texts = [s.value for s in at.success]
    assert any("v-test" in t and "111 chunk" in t and "1515 BM25 词项" in t for t in texts)


def test_rebuild_failure_keeps_old_and_page_survives(monkeypatch):
    def boom():
        raise RuntimeError("模拟重建失败")

    monkeypatch.setattr(rag_one.indexing.indexer, "build_and_publish_indexes", boom)

    at = run_app()
    click_button(at, "重建索引")

    assert not at.exception
    errors = [e.value for e in at.error]
    assert len(errors) == 1
    assert "active version 未切换" in errors[0]
    assert not at.success
