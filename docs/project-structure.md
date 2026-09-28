# 项目目录结构与职责

本文描述 v2.5 收尾后的实际目录。历史版本报告中的 `src/*.py`、`ingest.py` 等路径只代表当时版本，当前运行代码统一位于 `src/rag_one/`。

## 1. 目录总览

```text
rag-one/
├── README.md                    # 当前状态、安装方式、最短运行路径与文档导航
├── pyproject.toml               # 主包配置、直接依赖、可编辑安装与 pytest 配置
├── requirements.txt             # 兼容旧环境的依赖清单
├── app.py                       # Streamlit 界面入口
├── .env.example                 # 外部服务配置模板；真实 .env 不提交
│
├── src/rag_one/                 # 唯一的运行时代码包
├── scripts/                     # 索引构建、迁移、实验编排和状态检查
├── evaluation/                  # 数据集读取、指标、评估和人工评审工具
├── tests/                       # 离线单元测试与集成测试
├── data/                        # 原始语料、冻结快照、评估集与实验结果
├── docs/                        # 规划、版本报告、实验、ADR 和调优手册
└── storage/                     # 本机索引与活动版本状态；可以重建，不作为源码交付
```

## 2. 运行时代码 `src/rag_one/`

```text
src/rag_one/
├── __init__.py
├── config.py                    # .env、模型、路径和索引配置
├── state.py                     # 语料、切分、双索引和 manifest 一致性检查
├── pipeline.py                  # 四种检索模式的统一执行与阶段追踪
├── rag.py                       # 检索→生成的应用层问答入口
│
├── ingestion/
│   ├── loaders.py               # Markdown、TXT、PDF 加载
│   └── splitter.py              # 文本切分、重叠和稳定 chunk ID
│
├── indexing/
│   ├── embeddings.py            # Embedding API 封装与批处理
│   ├── vector_store.py          # Chroma 集合读写
│   ├── bm25_store.py            # 中文分词、BM25 索引和检索
│   ├── manifest.py              # 索引版本清单、active pointer 与原子写入
│   └── indexer.py               # 向量+BM25同版本构建、校验、发布与回滚
│
├── retrieval/
│   ├── vector.py                # 向量检索
│   ├── fusion.py                # RRF 排名融合纯函数
│   ├── hybrid.py                # 向量+BM25双路召回与融合
│   ├── reranker.py              # Rerank API、响应校验和相关性排序
│   └── hybrid_reranker.py       # 融合候选→重排→Top-K，失败时可回退
│
└── generation/
    └── generator.py             # Prompt、LLM调用、拒答和引用结构校验
```

职责边界：

- `ingestion` 只负责把文件转换成稳定 chunk，不访问向量库；
- `indexing` 负责持久化和版本发布，不负责生成答案；
- `retrieval` 负责召回、融合与排序，不调用 LLM 生成答案；
- `generation` 只消费已经选出的 Top-K；
- `pipeline.py` 负责组合四种检索模式并保留阶段信息；
- `rag.py` 是问答应用入口，不重复实现底层算法。

## 3. 运维脚本 `scripts/`

```text
scripts/
├── rebuild_indexes.py           # 构建并发布同版本 Chroma+BM25
├── migrate_legacy_index.py      # 把 v2 旧索引登记为 v2.5 manifest 状态
├── verify_project_state.py      # 严格验证语料、切分、索引和运行环境
├── freeze_corpus.py             # 生成语料指纹与切分快照
└── run_chunk_experiments.py     # 编排多组 chunk 的真实四模式实验
```

这些文件是可执行动作，不属于在线问答链路。脚本应调用 `rag_one` 包中的能力，不能复制一份索引或检索实现。

其中 `rebuild_indexes.py`、真实 chunk 实验等会把语料发送到 `.env` 指定的 Embedding/Rerank 服务，运行前必须确认数据允许出站。

## 4. 评估工具 `evaluation/`

```text
evaluation/
├── dataset.py                   # 读取 JSONL、锚点映射和数据准备
├── metrics.py                   # Recall、MRR、证据组、完整证据等纯函数
├── evaluate_retrieval.py        # vector/bm25/hybrid/hybrid_rerank 检索评估
├── evaluate_e2e.py              # 检索→生成端到端评估
├── evaluate_chunk_offline.py    # 多组 chunk 的离线 BM25 预检
├── review_e2e.py                # 人工答案、引用、拒答和幻觉评审模板/汇总
└── validate_dataset.py          # regression、holdout 结构与证据标注校验
```

约定：

- 指标纯函数放在 `metrics.py`，避免每个实验各写一套公式；
- 评估代码可以调用生产检索链路，生产代码不能反向依赖评估模块；
- JSON 保存机器可读原始结果，Markdown 保存逐题可读报告；
- 自动引用编号检查不能替代人工语义支持性判定。

## 5. 测试 `tests/`

```text
tests/
├── unit/
│   ├── test_bm25.py
│   ├── test_dataset.py
│   ├── test_evaluation.py
│   ├── test_experiment_scripts.py
│   ├── test_fusion.py
│   ├── test_generator.py
│   ├── test_loaders.py
│   ├── test_metrics.py
│   ├── test_pipeline.py
│   ├── test_rag.py
│   ├── test_reranker.py
│   ├── test_review_e2e.py
│   ├── test_splitter.py
│   └── test_state.py
└── integration/
    ├── test_app.py
    ├── test_datasets.py
    └── test_indexer.py
```

- `unit/` 使用替身验证纯逻辑、API异常、参数边界和评估口径；
- `integration/` 验证界面、完整数据集和双索引发布/回滚；
- 离线测试不得依赖真实 API Key 或网络；
- 当前全量测试为 115 项。

## 6. 数据 `data/`

```text
data/
├── README.md                    # 数据集说明
├── raw/                         # 10份冻结的虚构员工手册
├── snapshots/
│   ├── corpus-v2.md             # v2语料指纹与切分快照
│   └── eval-v2.5.md             # v2.5评估集冻结信息
└── eval/
    ├── regression.jsonl         # 32题开发/回归集，可重复运行
    ├── holdout.jsonl            # 原15题v2.5终验集，已经消费
    ├── blind-v2.5.jsonl         # C4冻结后的20题新盲测，已经消费
    ├── evidence-anchors.json     # 跨chunk配置的稳定文本证据锚点
    └── results/
        ├── v2/                  # v2四模式与E1/E4历史结果
        └── v2.5/                # chunk离线实验与v2.5 E2E结果
```

数据纪律：

- `raw/` 是当前知识库输入；改变语料后必须重建索引并更新快照；
- regression 用于开发、修复和重复验证；
- 原 v2.5 Holdout 与新 20 题盲测均已执行，不能用于调参后再次宣称独立终验；
- chunk 参数变化时使用 `evidence-anchors.json` 重新映射证据，不能直接复用旧序号 ID；
- `results/` 保存原始实验产物，不能只保留手工摘录的汇总数字。

## 7. 文档 `docs/`

```text
docs/
├── project-structure.md         # 本文件：当前目录与职责
├── plans/
│   ├── RAG-MVP学习规划.md       # v1.0开始前的学习规划
│   ├── RAG-v2.0学习规划.md      # v2.0召回与排序规划
│   └── RAG-v2.5学习规划.md      # v2.5收敛、加固与验收规划
├── reports/
│   ├── v1.0.md                  # v1.0唯一版本报告
│   ├── v2.0.md                  # v2.0唯一版本报告
│   └── v2.5.md                  # v2.5唯一版本报告，含复盘与学习验收
├── experiments/
│   ├── chunk-v2.5.md            # 分块大小/重叠实验过程与结论
│   └── citation-v2.5.md         # C0—C4生成、引用与新盲测实验
├── decisions/
│   ├── 001-versioned-dual-index.md
│   ├── 002-package-layout.md
│   └── 003-evaluation-split-and-anchors.md
└── notes/
    └── RAG调优手册.md           # 跨版本调优原则、参数证据和实验模板
```

文档职责：

| 目录 | 回答的问题 |
|---|---|
| `plans/` | 版本开始前准备做什么 |
| `reports/` | 每个版本最终做成了什么；一版本一文件 |
| `experiments/` | 某个变量如何测试、结果和取舍是什么 |
| `decisions/` | 为什么选择某个长期架构方案（ADR） |
| `notes/` | 跨版本可复用的方法与知识 |

## 8. 本机索引 `storage/`

```text
storage/
├── active-index.json            # 当前活动索引指针
├── index-manifests/             # 每个不可变索引版本的manifest
├── chroma/                      # Chroma数据库与向量集合
└── bm25/                        # 当前或版本化BM25 JSON索引
```

`storage/` 是本机运行状态，不是源码：

- 可由冻结语料和配置重新构建；
- 不应手工修改 Chroma 内部文件；
- `active-index.json` 只能指向通过校验的完整双索引版本；
- manifest 用于核对语料指纹、chunk参数、chunk ID、模型和两套索引位置；
- 历史候选用于回滚，当前尚未实现自动清理策略。

## 9. 关键调用关系

### 9.1 构建与发布

```text
scripts/rebuild_indexes.py
        ↓
ingestion.loaders + splitter
        ↓
indexing.indexer
        ├→ embeddings → vector_store → Chroma不可变集合
        └→ bm25_store → 不可变BM25 JSON
        ↓
校验数量、ID与manifest
        ↓
原子更新storage/active-index.json
```

### 9.2 问答

```text
app.py / rag.py
      ↓
pipeline.py
      ├→ vector
      ├→ bm25_store
      ├→ hybrid + RRF
      └→ hybrid_reranker
      ↓
generation.generator
      ↓
答案 + 引用结构检查 + Token信息
```

### 9.3 评估

```text
data/eval/*.jsonl
      ↓
evaluation.dataset
      ↓
生产检索/生成链路
      ↓
evaluation.metrics + review_e2e
      ↓
data/eval/results/<version>/
```

## 10. 新增内容应该放在哪里

| 新内容 | 位置 |
|---|---|
| 在线运行逻辑 | `src/rag_one/` 对应子包 |
| 一次性或运维命令 | `scripts/` |
| 指标、数据校验、实验执行 | `evaluation/` |
| 自动化验证 | `tests/unit` 或 `tests/integration` |
| 原始知识库文件 | `data/raw/` |
| 评估问题与证据标注 | `data/eval/` |
| 机器生成实验结果 | `data/eval/results/<version>/` |
| 版本开始前的规划 | `docs/plans/` |
| 版本最终结论 | `docs/reports/<version>.md` |
| 单变量调优过程 | `docs/experiments/` |
| 长期架构决策 | `docs/decisions/` |
| 跨版本方法手册 | `docs/notes/` |

## 11. 总体边界

- `app.py` 只负责交互，不复制业务逻辑；
- `src/rag_one/` 是唯一运行时代码包；
- `scripts/` 是动作入口，`evaluation/` 是实验工具；
- `tests/` 不依赖真实外部服务；
- `data/eval/results/` 保存事实产物，`docs/experiments/` 保存人工解释；
- `docs/reports/` 每个版本只保留一份Markdown；
- `storage/` 可以重建，不作为源码交付；
- 任何索引、Prompt或参数变化都应在固定regression上验证，并保留复现metadata。
