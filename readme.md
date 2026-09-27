# rag-one

一个透明、可验证的中文 RAG 学习项目。当前链路为：

```text
向量召回 ─┐
           ├→ RRF 融合 → Reranker → Top-K → LLM → 引用校验
BM25 召回 ─┘
```

## 当前状态

v2.5 的工程改造已经落地，目前状态是“工程候选版”，不是完整质量发布版。

| 范围 | 状态 |
|---|---|
| `src/rag_one/` 包结构与 editable install | 已完成 |
| 向量 + BM25 同版本构建、manifest、原子激活与回滚 | 已完成 |
| regression 32 题、holdout 15 题、证据组与稳定证据锚点 | 已完成 |
| 复现元数据、状态校验、异常响应和失败注入测试 | 已完成 |
| 离线测试 | 113 个通过 |
| chunk 参数离线 BM25 预检 | 已完成，工程配置冻结为 800/150 |
| 五组 chunk 的真实四模式实验 | 按项目决策取消，不宣称 800/150 为全局最优 |
| C1 regression 完整验收 | 运行中断，未形成有效结论 |
| holdout 一次性终验 | 已完成；检索 100%，严格答案完整率 66.7%，生成质量未通过 |
| 学习者书面/口头验收 | 待学习者本人完成 |

v2.0 历史 E4 结果为 Recall@5 100%、答案正确率 100%、严格引用准确率 79.3%。v2.5 Holdout 证明检索层可以完整召回证据，但生成端存在错误拒答和多事实遗漏，因此同样不会通过降低口径把未达标项写成通过。

## 安装与最短运行路径

项目使用 Python 3.11+：

```powershell
python -m pip install -e ".[test]"
Copy-Item .env.example .env
# 编辑 .env，填入服务密钥与模型

python -m scripts.rebuild_indexes
python -m scripts.verify_project_state
python -m evaluation.validate_dataset data/eval/regression.jsonl data/eval/holdout.jsonl
python -m pytest tests -q
python -m streamlit run app.py
```

`rebuild_indexes`、向量/重排评估和端到端问答会把语料或问题发送到 `.env` 指定的服务。仅在你确认数据可发送给该服务时运行。

检索评估示例：

```powershell
python -m evaluation.evaluate_retrieval --mode hybrid_rerank
python -m evaluation.evaluate_e2e --mode hybrid_rerank --dataset data/eval/regression.jsonl
```

保留集只允许在版本候选冻结后运行一次，不用于选择 chunk 参数或 Prompt。

## 项目导航

- [项目目录职责](docs/project-structure.md)
- [v2.5 学习规划](docs/plans/RAG-v2.5学习规划.md)
- [v1.0 版本报告](docs/reports/v1.0.md)
- [v2.0 版本报告](docs/reports/v2.0.md)
- [v2.5 实施报告](docs/reports/v2.5.md)
- [chunk 实验记录](docs/experiments/chunk-v2.5.md)
- [引用实验记录](docs/experiments/citation-v2.5.md)
- [RAG 调优手册](docs/notes/RAG调优手册.md)
- [v2.5 学习验收](docs/reports/v2.5.md)

## 已知限制

- 当前只处理可抽取文本的 Markdown、TXT 和 PDF，不含 OCR、图片与表格专项解析。
- Reranker 失败时应用默认回退到融合结果；严格实验可关闭回退。
- 引用编号范围可以自动检查，但“引用是否真正支持结论”仍需人工判定。
- 当前 active index 是本机运行状态，不提交仓库；克隆后必须自行重建。
- v2.5 Holdout 已消费，严格答案完整率 66.7%；不能用该组题调参后重复宣称独立终验通过。
- v2.5 生成质量和学习者验收未通过，不能把本分支标记为完整发布版。
