"""Streamlit 界面：知识库管理 / 四链路问答 / 全过程追踪。

只调用 src 与 ingest 模块，不写核心逻辑：
- 检索与生成：src.pipeline.run_chain（vector / bm25 / hybrid / hybrid_rerank 四条链路）；
- 索引重建：src.indexer.build_index（先建后切）+ ingest_bm25.rebuild_bm25_index（原子替换）。

运行：
    python -X utf8 -m streamlit run app.py
"""

from pathlib import Path

import streamlit as st

from ingest_bm25 import rebuild_bm25_index
from src import vector_store
from src.bm25_store import load_index
from src.config import COLLECTION_NAME, DATA_RAW_DIR, PROJECT_ROOT
from src.indexer import build_index
from src.pipeline import run_chain

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
                stats = build_index()
                st.success(
                    f"向量索引：{stats['docs']} 篇 / {stats['chunks']} chunk / "
                    f"集合内 {stats['collection_count']} 条向量"
                )
            except Exception as exc:
                st.error(f"向量索引重建失败：{exc}（旧索引未受影响，可直接重试）")
            try:
                bm_stats = rebuild_bm25_index()
                st.success(f"BM25 索引：{bm_stats['chunks']} chunk / {bm_stats['terms']} 词项")
            except Exception as exc:
                st.error(f"BM25 索引重建失败：{exc}（旧索引未受影响，可直接重试）")

    st.caption("重建为全量重建，两套索引都采用「先建后切 / 原子替换」：任一步失败都会保留旧索引。")

    st.header("索引状态")
    try:
        client = vector_store.get_client()
        vector_count = vector_store.count(vector_store.get_collection(client))
        st.markdown(f"- 向量库 `{COLLECTION_NAME}`：{vector_count} 条向量")
    except Exception as exc:  # 库打不开也不让页面崩，给出提示即可
        st.markdown(f"- 向量库 `{COLLECTION_NAME}`：读取失败（{exc}）")

    try:
        bm_meta = load_index()["meta"]
        st.markdown(
            f"- BM25 索引：{bm_meta['chunk_count']} chunk / {bm_meta['term_count']} 词项"
            f"（构建于 {bm_meta['built_at']}）"
        )
    except FileNotFoundError:
        st.markdown("- BM25 索引：不存在（点上方“重建索引”生成）")

    doc_files = [p for p in DATA_RAW_DIR.iterdir() if p.is_file()] if DATA_RAW_DIR.exists() else []
    st.markdown(f"- 文档：data/raw 下 {len(doc_files)} 个文件")

    corpus_file = PROJECT_ROOT / "data" / "eval" / "corpus-version.md"
    if corpus_file.exists():
        date = ""
        for line in corpus_file.read_text(encoding="utf-8").splitlines():
            if "生成日期" in line:
                date = line.split("：", 1)[-1].strip()
                break
        st.markdown(f"- 语料版本：v2.0 冻结快照（{date}）")

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
                st.error("BM25 索引不存在：请先点侧边栏「重建索引」，或运行 python -X utf8 ingest_bm25.py")
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
    usage = result["usage"]
    token_text = f'prompt={usage["prompt_tokens"]}, completion={usage["completion_tokens"]}'
    if result["rerank_tokens"]:
        token_text += f', rerank={result["rerank_tokens"]}'
    st.caption(f'模式：{result["mode"]} · 问题：{result["question"]}（tokens: {token_text}）')

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
