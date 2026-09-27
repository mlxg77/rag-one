# 项目目录职责

```text
rag-one/
├── README.md
├── pyproject.toml
├── app.py
├── src/rag_one/
│   ├── config.py
│   ├── state.py
│   ├── pipeline.py
│   ├── rag.py
│   ├── ingestion/      # 文档加载与切分
│   ├── indexing/       # Embedding、双索引、manifest 与发布
│   ├── retrieval/      # 向量、BM25、RRF、混合检索与重排
│   └── generation/     # Prompt、LLM 调用与引用结构校验
├── scripts/                 # 索引重建、语料冻结、迁移与状态校验
├── evaluation/              # 数据集、指标、检索/E2E/chunk 评估
├── tests/
│   ├── unit/
│   └── integration/
├── data/
│   ├── raw/             # 冻结的 10 份虚构员工手册
│   ├── snapshots/       # 语料/评估冻结记录
│   └── eval/            # regression、holdout、证据锚点与结果
├── docs/
│   ├── plans/           # 版本学习规划
│   ├── reports/         # 起点、最终报告与历史
│   ├── experiments/     # 单变量实验
│   ├── decisions/       # 架构取舍
│   └── notes/           # 学习验收与知识笔记
└── storage/                 # 本机可重建索引，不作为源码交付
```

## 边界约定

- `app.py` 只负责界面，不复制检索、索引或生成逻辑。
- `src/rag_one/` 是唯一运行时代码包；根目录旧兼容脚本已经删除。
- `scripts/` 负责运维动作，`evaluation/` 负责实验，不把评估代码放入线上链路。
- `data/eval/results/` 保存机器可读原始结果；`docs/experiments/` 保存人工结论。
- `storage/active-index.json` 与 manifest 是本机运行状态，不进入 Git；可复现身份随评估 metadata 保存。
