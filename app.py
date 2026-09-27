"""Streamlit 界面：知识库管理 / 四链路问答 / 全过程追踪。

只调用 rag_one 应用层，不写核心逻辑：
- 检索与生成：rag_one.pipeline.run_chain；
- 索引重建：rag_one.indexing.indexer.build_and_publish_indexes。

运行：
    python -X utf8 -m streamlit run app.py
"""

from pathlib import Path

import streamlit as st

from rag_one.config import DATA_RAW_DIR
from rag_one.indexing.indexer import build_and_publish_indexes
from rag_one.pipeline import run_chain
from rag_one.state import verify_project_state

MODE_LABELS = {
    "混合重排（融合 + Reranker 精排）": "hybrid_rerank",
    "混合检索（两路召回 + RRF 融合）": "hybrid",
    "向量检索（仅语义向量）": "vector",
    "BM25 关键词（仅关键词）": "bm25",
}


def candidate_row(item: dict, mode: str) -> dict:
    """候选池一行：把各阶段名次压成表格列（缺失的阶段显示 —）。"""
    page = item["page"]
    location = item["source"] if page is None else f'{item["source"]}·p{page}'
    if "rrf_rank" in item:
        fuse_rank = item["rrf_rank"]        # 重排链路：融合名次已留档
    elif mode == "hybrid":
        fuse_rank = item["rank"]            # 融合链路：候选即融合结果，rank 就是融合名次
    else:
        fuse_rank = None
    return {
        "来源": location,
        # 名次列统一转字符串：int 与 "—" 混排会让 dataframe 序列化报类型告警
        "向量#": str(item.get("vector_rank") or "—"),
        "BM25#": str(item.get("bm25_rank") or "—"),
        "融合#": str(fuse_rank or "—"),
        "重排分": f'{item["rerank_score"]:.4f}' if "rerank_score" in item else "—",
        "最终#": str(item.get("final_rank") or "—"),
        "片段": item["text"][:60] + ("…" if len(item["text"]) > 60 else ""),
    }


def hit_rank_line(hit: dict) -> str:
    """最终命中一条的名次链文案（只显示该链路存在的阶段）。"""
    parts: list[str] = []
    if "vector_rank" in hit:
        parts.append(f'向量#{hit["vector_rank"] or "—"}')
    if "bm25_rank" in hit:
        parts.append(f'BM25#{hit["bm25_rank"] or "—"}')
    if "rrf_rank" in hit:
        parts.append(f'融合#{hit["rrf_rank"]}')
    if "rerank_score" in hit:
        parts.append(f'重排分 {hit["rerank_score"]:.4f}')
    return " · ".join(parts)


st.set_page_config(page_title="rag-one 文档问答", layout="centered")

st.title("rag-one：文档问答助手")
st.caption("回答由 LLM 根据检索结果生成；候选池各阶段名次、分阶段耗时都在下方可展开核对。")

# ---------------- 侧边栏：知识库管理 / 索引状态 / 检索设置 ----------------
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
        with st.spinner("正在重建索引（先写新索引 → 校验 → 成功后切换）..."):
            try:
                stats = build_and_publish_indexes()
                st.success(
                    f"双索引版本 {stats['index_version']} 已发布："
                    f"{stats['docs']} 篇 / {stats['chunks']} chunk / "
                    f"{stats['bm25_terms']} BM25 词项"
                )
            except Exception as exc:
                st.error(f"双索引重建失败：{exc}（active version 未切换，可直接重试）")

    st.caption("向量与 BM25 先构建为同一不可变版本；全部校验通过后才原子切换 active pointer。")

    st.header("索引状态")
    try:
        index_state = verify_project_state()
        short_version = index_state["index_version"]
        st.markdown(
            f"- Active：`{short_version}`\n"
            f"- 双索引：{index_state['chunk_count']} chunk / "
            f"{index_state['bm25']['term_count']} BM25 词项\n"
            f"- 切分：{index_state['chunk_size']} / {index_state['chunk_overlap']}"
        )
    except Exception as exc:  # 状态不一致也不让页面崩，明确要求重建
        st.markdown(f"- 索引状态：不可用或不一致（{exc}）")

    doc_files = [p for p in DATA_RAW_DIR.iterdir() if p.is_file()] if DATA_RAW_DIR.exists() else []
    st.markdown(f"- 文档：data/raw 下 {len(doc_files)} 个文件")

    st.header("检索设置")
    mode_label = st.selectbox("检索模式", list(MODE_LABELS))
    mode = MODE_LABELS[mode_label]
    top_k = st.slider("最终 Top-K（进 Prompt 的条数）", min_value=1, max_value=10, value=5)
    if mode in ("hybrid", "hybrid_rerank"):
        candidate_k = st.slider(
            "候选数（两路召回到融合/重排的条数）", min_value=5, max_value=30, value=20, step=5
        )
    else:
        candidate_k = 20  # 单路模式不适用

# ---------------- 主区：提问与回答 ----------------
question = st.text_input("请输入你的问题", placeholder="例如：普通员工去上海出差，酒店每晚含税最高可以报销多少？")

if st.button("提问"):
    if not question.strip():
        st.warning("请先输入问题。")
    else:
        with st.spinner(f"检索（{mode_label}）并生成回答中（约几秒）..."):
            try:
                st.session_state["result"] = run_chain(
                    mode,
                    question.strip(),
                    top_k=top_k,
                    vector_k=candidate_k,
                    bm25_k=candidate_k,
                    candidate_k=candidate_k,
                )
            except FileNotFoundError:
                st.error("向量或 BM25 索引不存在：请先点侧边栏「重建索引」，或运行 python -m scripts.rebuild_indexes")
            except Exception as exc:
                st.error(f"问答失败：{exc}")

result = st.session_state.get("result")

if result is None:
    st.info("提问后，这里会显示回答、候选池各阶段名次与分阶段耗时。")
else:
    for warning in result["warnings"]:
        st.warning(warning)

    st.subheader("回答")
    st.markdown(result["answer"])
    citation_validation = result.get("citation_validation") or {}
    if citation_validation.get("invalid_citations"):
        st.error(f"回答含越界引用编号：{citation_validation['invalid_citations']}")
    if citation_validation.get("refusal_has_citations"):
        st.warning("回答已拒答但仍附带引用，请人工复核是否为无关引用。")
    usage = result["usage"]
    token_text = f'prompt={usage["prompt_tokens"]}, completion={usage["completion_tokens"]}'
    if result["rerank_tokens"]:
        token_text += f', rerank={result["rerank_tokens"]}'
    prompt_version = result.get("prompt_version") or "unknown"
    st.caption(
        f'模式：{result["mode"]} · Prompt：{prompt_version} · '
        f'问题：{result["question"]}（tokens: {token_text}）'
    )

    stage_text = " → ".join(f'{s["name"]} {s["elapsed_ms"]}ms' for s in result["stages"])
    st.markdown(f"**分阶段耗时**：{stage_text} · 合计 {result['total_ms']} ms")

    st.subheader(f'候选池与各阶段名次（共 {len(result["candidates"])} 条候选，前 {len(result["hits"])} 条进 Prompt）')
    rows = [candidate_row(item, result["mode"]) for item in result["candidates"]]
    st.dataframe(rows, width="stretch", hide_index=True)

    st.subheader("最终引用片段（与回答里的 [编号] 对应）")
    for hit in result["hits"]:
        page = hit["page"]
        location = hit["source"] if page is None else f'{hit["source"]}（第 {page} 页）'
        with st.expander(f'[{hit["rank"]}] {location} · score={hit["score"]:.4f}'):
            line = hit_rank_line(hit)
            if line:
                st.caption(line)
            st.text(hit["text"])
