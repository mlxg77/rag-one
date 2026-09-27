"""Streamlit 界面：文档上传 / 重建索引 / 问答（只调用 src 模块，不写核心逻辑）。

运行：
    python -X utf8 -m streamlit run app.py
"""

from pathlib import Path

import streamlit as st

from src.config import DATA_RAW_DIR
from src.indexer import build_index
from src.rag import ask

st.set_page_config(page_title="rag-one 文档问答", layout="centered")

st.title("rag-one：文档问答助手")
st.caption("回答由 LLM 根据 data/raw 的检索结果生成；下面的检索结果可与回答里的 [编号] 逐一核对。")

# ---------------- 侧边栏：知识库管理 ----------------
with st.sidebar:
    st.header("知识库管理")

    uploaded_files = st.file_uploader(
        "上传文档（.md / .txt / .pdf，可多选）",
        type=["md", "txt", "pdf"],
        accept_multiple_files=True,
    )
    if uploaded_files and st.button("保存到知识库"):
        saved_names = []
        for f in uploaded_files:
            target = DATA_RAW_DIR / Path(f.name).name
            target.write_bytes(f.getvalue())
            saved_names.append(target.name)
        st.success("已保存：" + "、".join(saved_names) + "（点“重建索引”后生效）")

    if st.button("重建索引"):
        with st.spinner("正在重建索引（加载 → 切分 → 向量化 → 写入）..."):
            try:
                stats = build_index()
                st.success(
                    f"完成：{stats['docs']} 篇文档 / {stats['chunks']} 个 chunk / "
                    f"集合内 {stats['collection_count']} 条向量"
                )
            except Exception as exc:
                st.error(f"重建失败：{exc}（索引可能不完整，修复后请重试重建）")

    st.caption("重建为全量重建：先清空旧集合，再写入 data/raw 下全部文档。")

# ---------------- 主区：提问与回答 ----------------
question = st.text_input("请输入你的问题", placeholder="例如：普通员工去上海出差，酒店每晚含税最高可以报销多少？")

if st.button("提问"):
    if not question.strip():
        st.warning("请先输入问题。")
    else:
        with st.spinner("检索并生成回答中（约几秒）..."):
            try:
                st.session_state["result"] = ask(question.strip())
            except Exception as exc:
                st.error(f"问答失败：{exc}")

result = st.session_state.get("result")

if result is None:
    st.info("提问后，这里会显示回答；每条检索结果可展开查看原文片段与分数。")
else:
    st.subheader("回答")
    st.markdown(result["answer"])
    usage = result["usage"]
    st.caption(
        f'问题：{result["question"]}（tokens: prompt={usage["prompt_tokens"]}, '
        f'completion={usage["completion_tokens"]}）'
    )

    st.subheader(f'检索结果（共 {len(result["hits"])} 条，与回答里的 [编号] 对应）')
    for hit in result["hits"]:
        location = hit["source"] if hit["page"] is None else f'{hit["source"]}（第 {hit["page"]} 页）'
        with st.expander(f'[{hit["rank"]}] {location} · score={hit["score"]:.4f}'):
            st.text(hit["text"])