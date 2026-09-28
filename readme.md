# rag-one

一个透明、可验证的中文 RAG 学习项目。当前链路为：

```text
向量召回 ─┐
           ├→ RRF 融合 → Reranker → Top-K → LLM → 引用校验
BM25 召回 ─┘
```

## 当前状态

v2.5 已正式完结，定位为“学习项目 / 内部演示完成版”，不是生产正式发布版。

| 范围 | 状态 |
|---|---|
| `src/rag_one/` 包结构与 editable install | 已完成 |
| 向量 + BM25 同版本构建、manifest、原子激活与回滚 | 已完成 |
| Regression 32 题、原 Holdout 15 题、新盲测 20 题、证据组与稳定证据锚点 | 已完成 |
| 复现元数据、状态校验、异常响应和失败注入测试 | 已完成 |
| 离线测试 | 115 个通过 |
| chunk 参数离线 BM25 预检 | 已完成，工程配置冻结为 800/150 |
| 五组 chunk 的真实四模式实验 | 按项目决策取消，不宣称 800/150 为全局最优 |
| C4 Regression 人工验收 | 已完成；答案 90.63%、引用 100%、拒答 100%、幻觉 0 |
| 新盲测一次性终验 | 已完成；答案 95%、引用 84.21%、拒答 100%、幻觉 1；项目接受当前结果并收尾 |
| v2.5 版本状态 | 已完结；可用于学习和内部演示，不作生产质量承诺 |
| 学习者书面/口头验收 | 待学习者本人完成 |

v2.0 历史 E4 结果为 Recall@5 100%、答案正确率 100%、严格引用准确率 79.3%。v2.5 的 C4 在 Regression 上达到冻结门槛；新盲测答案正确率为 95%，项目负责人接受当前效果并结束本版本。严格引用 84.21% 和 1 个边界金额错误被如实保留为后续版本输入。

## 安装与最短运行路径

项目使用 Python 3.11+：

```powershell
python -m pip install -e ".[test]"
Copy-Item .env.example .env
# 编辑 .env，填入服务密钥与模型

python -m scripts.rebuild_indexes
python -m scripts.verify_project_state
python -m evaluation.validate_dataset data/eval/regression.jsonl data/eval/holdout.jsonl data/eval/blind-v2.5.jsonl
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
- 原 15 题 Holdout 与新 20 题盲测均已消费，不能据此调参后重复宣称独立终验通过。
- 新盲测严格引用准确率为 84.21%，并有 1 个边界金额错误事实；v2.5 已按学习/内部演示目标完结，但不能据此宣称生产质量已经达标。
