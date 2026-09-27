# rag-one：RAG 最小可行产品（MVP）学习项目

> 一个"个人文档问答助手"的手写实现：导入本地 Markdown / TXT / PDF 文档，用户提问后先检索相关内容，再让大模型基于检索结果回答，并展示引用来源。
>
> 学习原则：**先验证检索，再接入生成；先让链路透明，再考虑框架封装。** 第一版不使用 LangChain / LangGraph。
>
> 本项目采用"你说我写"的学习方式：全部核心代码手写，助手负责分步讲授、验收（读代码 + 写临时脚本跑真实断言）。

完整链路：

```text
文档加载
  ↓
文本清洗与切分
  ↓
Embedding 向量化
  ↓
写入向量数据库
  ↓
用户提问
  ↓
相似度检索 Top-K
  ↓
组装上下文和 Prompt
  ↓
LLM 生成带引用的回答
```

---

## 当前进度

### v1.0 · RAG-MVP（已完成）

| 阶段 | 内容 | 产出 | 状态 |
|---|---|---|---|
| 一 | 准备知识库和测试问题 | `data/raw/` 10 篇手册 + `data/eval/questions.jsonl` 25 题 | 已完成并验收 |
| 二 | 实现文档加载 | `src/loaders.py` | 已完成并验收 |
| 三 | 实现文本切分 | `src/splitter.py` | 已完成并验收 |
| 四 | 建立向量索引 | `src/config.py` / `src/embeddings.py` / `src/vector_store.py` / `src/indexer.py` / `ingest.py` | 已完成并验收 |
| 五 | 实现并验证检索 | `src/retriever.py` | 已完成并验收 |
| 六 | 实现答案生成 | `src/generator.py` / `src/rag.py` | 已完成并验收 |
| 七 | 增加简单界面 | `app.py`（Streamlit） | 已完成并验收 |

### v2.0 · 召回与排序（进行中）

在 v1.0 基础上学习“召回与排序”——BM25、RRF 融合、Reranker；规划见 `RAG-v2.0学习规划.md`（共 7 个阶段）。

| 阶段 | 内容 | 状态 |
|---|---|---|
| 一 | 冻结现有语料并完善评估标注 | 已完成并验收 |
| 二 | 建立 v1.0 可重复评估基线 | 已完成并验收 |
| 三 | 实现 BM25 检索 | 已完成并验收 |
| 四 | 实现混合检索与 RRF 融合 | 已完成并验收 |
| 五 | 接入 Reranker | 已完成并验收 |
| 六 | 端到端对照实验 | 已完成并验收 |
| 七 | 工程化与界面升级 | 未开始 |

---

## 环境与运行方式

### Python 环境（conda）

- 环境名：`rag-one`（Python 3.12.14），路径 `E:\Anaconda_envs\envs\rag-one`
- 本项目不使用 `.venv`（已删除），全程只用一个隔离环境，避免"依赖装在一个环境、代码跑在另一个环境"

安装依赖（在项目根目录执行）：

```powershell
conda activate rag-one
pip install -r requirements.txt
```

已锁定并实测的版本：

| 依赖 | 版本 | 用途 |
|---|---|---|
| python-dotenv | 1.2.3 | 读取 `.env` 配置 |
| openai | 3.19.2 | LLM / Embedding 调用（兼容 OpenAI 协议，配硅基流动） |
| httpx | 0.28.1 | Rerank API HTTP 直连（硅基流动 rerank 端点；openai SDK 底层依赖，直接 import 即显式声明） |
| chromadb | 1.5.9 | 向量数据库（本地持久化） |
| pymupdf | 1.28.2 | PDF 文本提取（导入名 `import pymupdf`） |
| streamlit | 1.64.0 | Web 界面（附带依赖 pandas / pyarrow 等自动安装） |
| pytest | 9.1.1 | 测试 |
| jieba | 0.42.1 | 中文分词（v2.0 BM25 关键词检索） |

### 运行规范（本机必读）

1. **一律用 `rag-one` 环境的 Python 运行**。本机裸 `python` 指向系统 Python 3.13（不含项目依赖，`import chromadb` 会失败）：

   ```powershell
   conda activate rag-one
   python -X utf8 ingest.py
   # 或不激活，直接用全路径
   E:\Anaconda_envs\envs\rag-one\python.exe -X utf8 ingest.py
   ```

2. **所有脚本必须加 `-X utf8` 运行**。本机中文 Windows 默认 GBK 编码，不加会导致中文输出乱码甚至丢输出：

   ```powershell
   python -X utf8 src/loaders.py
   ```

3. **`src` 包内模块用 `-m` 从项目根运行**（包内导入写 `src.xxx` 全路径）：

   ```powershell
   python -X utf8 -m src.splitter
   ```

4. **不要使用 `conda run`**。conda 24.5.0 在本机中文环境下捕获中文输出会崩溃（UnicodeEncodeError）或吞掉输出；直接激活环境或用环境内 python 全路径运行。

5. **启动 Web 界面用 `python -m streamlit`**（`streamlit` 命令不在 PATH）：

   ```powershell
   E:\Anaconda_envs\envs\rag-one\python.exe -X utf8 -m streamlit run app.py
   ```

---

## 项目结构

```text
rag-one/
├── data/
│   ├── raw/                  # 9 篇制度手册 + 10-faq.pdf（v2.0 冻结语料，指纹见 corpus-version.md）
│   ├── eval/
│   │   ├── questions.jsonl   # 32 题评估集（含 relevant_chunk_ids chunk 级标注）
│   │   ├── corpus-version.md # v2.0 语料版本快照（指纹 / 切分参数 / chunk 统计）
│   │   ├── baseline-v1.json  # v1.0 向量检索基线（机器可读；防覆盖，各实验的对照基准）
│   │   ├── baseline-v1.md    # 基线的人类可读报告（分题型统计 + 未命中清单 + 逐题明细）
│   │   ├── run-bm25.json     # v2.0 阶段三：BM25 评估结果（机器可读，与基线同口径可对照）
│   │   ├── run-bm25.md       # BM25 评估的人类可读报告
│   │   ├── run-hybrid.json   # v2.0 阶段四：混合检索（RRF 融合）评估结果（机器可读，含两路名次）
│   │   ├── run-hybrid.md     # 混合检索评估的人类可读报告
│   │   ├── run-hybrid-rerank.json  # v2.0 阶段五：混合重排评估结果（机器可读，含重排前后名次与分数）
│   │   ├── run-hybrid-rerank.md    # 混合重排评估的人类可读报告
│   │   ├── run-e2e-vector.json     # v2.0 阶段六：E1 端到端评估（逐题答案 + token + 三段延迟，机器可读）
│   │   ├── run-e2e-vector.md       # E1 端到端的人类可读报告（逐题答案与引用）
│   │   ├── run-e2e-hybrid_rerank.json  # v2.0 阶段六：E4 端到端评估（另含重排回退与重排 token）
│   │   ├── run-e2e-hybrid_rerank.md    # E4 端到端的人类可读报告
│   │   └── eval-report.md    # 端到端人工评估表（v2.0 阶段六：32 题 × E1/E4 双链路判定）
│   └── README.md             # 数据集说明
├── storage/
│   ├── chroma/               # ChromaDB 持久化索引（git 忽略，可用 ingest.py 重建；当前 111 条 = v2.0 语料）
│   └── bm25/                 # BM25 关键词索引（git 忽略，可用 ingest_bm25.py 重建；当前 111 块 / 1515 词项）
├── src/
│   ├── __init__.py
│   ├── config.py             # 阶段四：集中配置读取（已完成）
│   ├── loaders.py            # 阶段二：文档加载（已完成）
│   ├── splitter.py           # 阶段三：文本切分（已完成）
│   ├── embeddings.py         # 阶段四：Embedding 调用（已完成）
│   ├── vector_store.py       # 阶段四：ChromaDB 封装（已完成）
│   ├── indexer.py            # 阶段四：索引构建（已完成）
│   ├── retriever.py          # 阶段五：Top-K 检索（已完成）
│   ├── generator.py          # 阶段六：Prompt 与答案生成（已完成）
│   ├── rag.py                # 阶段六：检索→生成主流程（已完成）
│   ├── bm25_store.py         # v2.0 阶段三：BM25 关键词检索（已完成）
│   ├── fusion.py             # v2.0 阶段四：RRF 排名融合（纯函数，已完成）
│   ├── hybrid_retriever.py   # v2.0 阶段四：双路召回 + RRF 融合（已完成）
│   ├── reranker.py           # v2.0 阶段五：Reranker 精排（独立封装 + 回退，已完成）
│   └── hybrid_reranker.py    # v2.0 阶段五：混合召回 + 重排组合（已完成）
├── ingest.py                 # 阶段四：索引入口（已完成）
├── ingest_bm25.py            # v2.0 阶段三：BM25 索引入口（已完成）
├── app.py                    # 阶段七：Streamlit 界面（已完成）
├── evaluation/               # v2.0：离线评估（检索 + 端到端，正式包）
│   ├── __init__.py
│   ├── metrics.py            # 指标纯函数：HitRank / Recall@K / RR@K / 百分位
│   ├── evaluate_retrieval.py # 检索评估 CLI：一条命令跑完全部题目 → JSON + Markdown
│   └── evaluate_e2e.py       # v2.0 阶段六：端到端评估 CLI（E1/E4，答案 + token + 三段延迟）
├── tests/
│   ├── test_bm25.py          # v2.0 阶段三：BM25 单元测试（pytest，6 用例）
│   ├── test_fusion.py        # v2.0 阶段四：RRF 融合单元测试（pytest，6 用例）
│   └── test_reranker.py      # v2.0 阶段五：重排链路单元测试（pytest，9 用例）
├── tools/
│   └── freeze_corpus.py      # v2.0：语料冻结脚本（生成 data/eval/corpus-version.md）
├── .env.example              # 环境变量模板（.env 含密钥，被 git 忽略）
├── RAG-MVP学习规划.md         # 总规划：目标、技术栈、七阶段验收清单
├── RAG-v2.0学习规划.md        # v2.0 规划：冻结语料、BM25 / RRF / Reranker 与对照实验
├── readme.md                 # 本文件
├── requirements.txt          # 纯 ASCII 英文注释（见"踩坑记录"）
└── .gitignore                # 忽略 .venv/ __pycache__/ .env storage/chroma/ storage/bm25/
```

---

## 工作记录

### v1.0 · RAG-MVP（已完成）

#### 阶段一：知识库与评估集（已完成并验收）

> v2.0 注：以下为 v1.0 当时的语料状态；v2.0 阶段一已将语料更新为 9 篇扩写版 Markdown + `10-faq.pdf`（原 `10-faq.md` 删除），现状以 `data/eval/corpus-version.md` 为准。

**知识库** `data/raw/`：虚构的“星云科技公司制度手册”共 10 篇 Markdown（版本 2026.1，生效日期 2026-01-01）：

```text
01-company-overview.md   02-onboarding.md     03-attendance.md
04-leave-policy.md       05-expense-policy.md 06-travel-policy.md
07-remote-work.md        08-information-security.md
09-it-support.md         10-faq.md
```

**评估集** `data/eval/questions.jsonl`：25 题，JSONL 格式（一行一题，便于追加），字段如下：

```json
{"id":"q01","question":"普通员工去上海出差，酒店每晚含税最高可以报销多少？","expected_answer":"700 元。","expected_sources":["06-travel-policy.md"],"type":"direct"}
```

题型分布：direct 9 / multi_source 5 / confusable 3 / unanswerable 3 / reasoning 2 / trap 2 / table 1。

**刻意设计的易混点**（用于观察切分、召回与引用是否准确）：

- 普通报销期限 30 个自然日，差旅报销是返程后 15 个自然日；
- 住宿标准按城市类别与职级变化（表格题）；
- 正式员工与试用期员工的远程办公规则不同；
- 病假、事假、年假的申请时限与证明材料不同；
- IT 服务台与安全事件的报告渠道不同。

**验收结果**：25 题逐题核对，答案与文档事实一致；JSON 合法、字段完整、id 唯一、`expected_sources` 均指向真实文件；拒答话题扫描通过（"食堂"0 命中为干净拒答，q22/q23 命中"无规定"指引段落为有依据拒答）。

遗留建议项（用户决定暂不处理）：q22/q23 拒答题的"有依据型 / 无依据型"标签可细分；文档总量约 13 页，低于规划建议的 20~100 页。

#### 阶段二：文档加载 `src/loaders.py`（已完成并验收）

分工策略：`load_file` 按扩展名分发到 `load_txt` / `load_md` / `load_pdf`，统一输出同一种记录结构：

```python
{
    "text": "文档内容",
    "metadata": {
        "source": "01-company-overview.md",
        "page": 12          # 仅 PDF 有；txt/md 不含此键，下游用 .get("page") 判断
    }
}
```

关键实现点：

- `PROJECT_ROOT = Path(__file__).resolve().parent.parent` 锚定项目根，避免相对路径失效；
- PDF 用 `import pymupdf` 逐页 `get_text()` 提取，页码从 1 开始，空页跳过；
- 读取失败 / 空文档 / 损坏文件统一捕获并返回空列表，不中断整目录扫描；
- `load_directory` 用 `sorted(glob("*"))` 保证加载顺序稳定。

运行效果（`python -X utf8 src/loaders.py`）：

```text
文档数: 10
记录数: 10
总字符数: 7220
```

**验收结果**：17/17 边界断言通过，覆盖正常 txt、空文件、纯空白、GBK 编码文件、损坏 PDF、含空页的真实 2 页 PDF、未知扩展名、目录批量加载。

#### 阶段三：文本切分 `src/splitter.py`（已完成并验收）

切分参数：

```text
chunk_size = 800      # 目标块大小（字符）
chunk_overlap = 150   # 相邻块重叠字符数
```

核心算法（`split_text`）：滑动窗口，窗口右端优先在 `\n\n` → `\n` → `。` 处断开，且断点必须位于窗口后半段（防止切出碎块）；切完一块后回退 `overlap` 个字符作为下一块起点（`max(end - overlap, start + 1)` 防止死循环）。

chunk ID 与元数据规则：

```python
{
    "id": "06-travel-policy.md:chunk-2",              # md/txt
    "id": "guide.pdf:page-12:chunk-2",                # pdf 带页码
    "text": "...",
    "metadata": {"source": "...", "chunk_index": 2, "page": 12}
}
```

运行效果（`python -X utf8 -m src.splitter`）：

```text
chunk 数量: 10
平均长度: 721.0 字符

合成文本 1202 字符 -> 2 块
  块 0: 600 字符
  块 1: 750 字符
```

**验收结果**：34/34 断言通过，覆盖：

- 真实数据：10 条记录 → 10 个 chunk（每篇 < 800 字符，故每篇 1 块，符合预期），ID 全局唯一、格式正确、metadata 完整；
- PDF 页码传递：伪造 1440 字符 PDF 记录 → ID 形如 `guide.pdf:page-12:chunk-N`，page 正确保留；
- 稳定性：两次独立切分结果完全一致；
- 重叠行为：硬切场景（无空白无分隔符）相邻块精确重叠 150 字符；段落文本 3602 字符 → 6 块，相邻重叠 148~150 字符；
- 边界输入：空文本 / 纯空白 → 0 块，短文本原样 1 块；
- `summarize`：正常输出 chunk 数量与平均长度，空列表不报错。

#### 阶段四：建立向量索引（已完成并验收）

**流程**：`加载 → 切分 → 向量化 → 写入 ChromaDB`；入口命令（全量重建）：

```powershell
python -X utf8 ingest.py
```

**新增文件与职责**：

- `src/config.py`：集中从 `.env` 读取 API 配置（Key / Base URL / 模型名）与路径（`data/raw`、`storage/chroma`）、集合名、批大小；`require_api_key()` 延迟报错，纯本地逻辑不受影响；
- `src/embeddings.py`：硅基流动 Embedding 调用（OpenAI 兼容协议）；`embed_texts` 自动分批并按返回 `index` 对齐顺序，`embed_query` 供检索阶段使用；
- `src/vector_store.py`：ChromaDB 封装——`PersistentClient` 本地持久化、集合用余弦距离、`upsert` 按 id 写入、`reset_collection` 先删后建（全量重建）；
- `src/indexer.py`：`build_index()` 串起全流程；metadata 附带 chunk 内容 MD5（`content_hash`，为将来增量索引用）；
- `ingest.py`：命令行入口，输出文档数 / chunk 数 / 集合向量数。

**关键配置**：`EMBEDDING_MODEL=BAAI/bge-m3`（输出 1024 维向量）、`COLLECTION_NAME=rag_mvp_docs`、`EMBED_BATCH_SIZE=32`；距离为**余弦距离**，换算关系 `相似度 = 1 - 距离`。

运行效果（连跑两遍，幂等，第二遍不产生重复数据）：

```text
=== 建立索引：...\data\raw -> ...\storage\chroma ===
文档数: 10
chunk 数: 10
集合内向量数: 10
索引已持久化到 storage/chroma，重启后仍然存在。
```

**验收结果**：23/23 断言通过，覆盖：

- 持久化：新进程直接读到 10 条向量，`chroma.sqlite3` 已落盘，集合名与余弦距离配置正确；
- 数据完整性：id 集合与切分结果完全一致、原文一致、`source / chunk_index / content_hash(MD5)` 正确、向量全部为 1024 维；
- 距离语义：用自己的向量自查询 top1 = 自己且距离 ≈ 0，距离随排名单调不减；
- 语义 smoke test：查询"普通员工去上海出差，酒店住宿每晚最高报销多少？"→《差旅制度》Rank 1（距离 0.2993），前 3 名均为报销相关文档；
- 分批对齐：把批大小临时改成 2 强制拆请求，同文本跨请求余弦 = 1.0，不同文本余弦 ≈ 0.58；
- 全量重建闭环：reset 后 count = 0 → `build_index()` 重建后回到 10 条，数据可按 id 取回。

#### 阶段五：Top-K 检索 `src/retriever.py`（已完成并验收）

**流程**：`问题 → embed_query → Chroma query(Top-K) → 结构化结果`；本阶段不接 LLM，先只验证检索质量。

**接口**：

```python
hits = retrieve(question, top_k=5)   # 默认 DEFAULT_TOP_K=5，可传参覆盖
# hits: [{"rank", "id", "score", "distance", "source", "page", "text"}, ...]
```

**关键实现点**：

- `collection.query(query_embeddings=[向量], n_results=top_k, include=[...])`：返回的每一列都是"外层 = 查询数、内层 = K 条"的嵌套列表，一次问一个问题时统一取 `[0]` 解包；
- 距离换相似度：`score = 1 - distance`（余弦距离越小越像）；展示用 score、排序沿用 Chroma 的距离升序；
- 与索引写入完全对称：写入是四平行列表（ids/embeddings/texts/metadatas），查询读出 ids/documents/metadatas/distances 仍是平行列表，`zip` 按位对齐；
- md 文档的 metadata 无 `page` 键 → 用 `meta.get("page")`，`format_hits` 按有无页码生成"文件名 / 文件名 第 N 页"两种展示；
- `format_hits` 为纯函数（不查库、只排版），阶段六可直接复用。

**运行效果**（`python -X utf8 -m src.retriever`）：

```text
问题：普通员工去上海出差，酒店每晚含税最高可以报销多少？

Rank 1 | score≈0.6852 | 06-travel-policy.md
  chunk: 06-travel-policy.md:chunk-0
  内容: ...（完整 chunk 原文）
```

**验收结果**：20/20 断言通过 + 25 题检索评估：

- 结构：7 字段齐全、rank 连续、score == 1 - distance、距离单调不减、id 与 source 对应；
- top_k 参数化：3 / 1 / 20 三档（20 超库存时截断为全部 10 条，不报错）；
- 语义：q01 原文与同义改写（"出差住酒店一晚最多能报多少钱"）Rank1 均为 06-travel-policy.md；
- **25 题 Recall@5：来源级 31/31 = 100%**（题级严格全中 24/24；q24 无期望来源不参与统计），远超 ≥80% 目标；
- 切分参数对比（临时把 CHUNK_SIZE 800→400 重建索引）：细切后来源级召回率反而降至 29/31 = 93.5%，且 q01 的 Rank1 从 06-travel 变为 10-faq——当时结论维持 800/150，完整对比与后续复跑见「调优实验 T1」；
- 边界观察：库外问题（"公司食堂每天几点开饭？"）也返回 5 条（top1 分数 ≈ 0.6410）——**检索器不会拒答，只会给"相对最像的"**；分数绝对值不足以区分"有依据/无依据"，拒答要靠阶段六的生成 Prompt 兜底。

#### 阶段六：答案生成 `src/generator.py` + `src/rag.py`（已完成并验收）

**流程**：`问题 → retrieve → build_prompt（编号 [1]..[K]）→ chat.completions → 带引用的回答`。

**接口**：

```python
result = ask(question, top_k=5)
# result: {"question", "hits", "answer", "usage": {"prompt_tokens", "completion_tokens"}}
```

**关键实现点**：

- Prompt 照抄规划第 5 节模板：四句指令（只根据参考资料 / 资料不足拒答 / 不用外部事实 / 列出资料编号）+ `{context}` + `{question}`；
- 编号 `[N]` 直接取 `hit["rank"]`，答案中"使用的资料编号 [N]"可逐条追溯回 `hits[N-1]`——引用可核查性的基础；
- **Qwen3-8B 必须关闭思考模式**：`extra_body={"enable_thinking": False}`，不开时每次问答约 15 秒 / 400 思考 token（详见踩坑 13 与附录知识笔记）；
- `LLM_TEMPERATURE = 0.2`（低于默认 0.6）：制度问答稳定、评估可复现；
- `ask()` 把 `hits` 与 `answer` 分开返回（"分别查看检索结果和最终回答"）；`__main__` 为命令行问答（`q` 退出），先打印检索详情、再给回答和 token 统计。

**运行效果**（`python -X utf8 -m src.rag`，实测节选）：

```text
问题> 普通员工去上海出差，酒店每晚含税最高可以报销多少？
…（检索逐条展示）…
回答：普通员工去上海出差，酒店每晚含税最高可以报销 700 元。
使用的资料编号：[1]
(tokens: prompt=2412, completion=28)
```

**验收结果**：18/18 断言通过，端到端三题：

- q01 直接题：答案含正确事实"700 元"、引用 [1]→ 06-travel-policy.md、且"700"与被引用 chunk 原文逐字核对一致；
- q11 多来源题：答出"每周最多一天"并正确得出"不能"结论、引用可追溯（仅引 07-remote-work.md、未引 02——引用准确，但未覆盖全部相关文档，第一版接受）；
- q24 拒答题："根据现有资料无法确定"正确触发；检索仍正常返回 5 条（拒答靠 Prompt，而非检索端）；
- 已知观察：拒答时模型仍会附带"使用的资料编号"一行，第一版接受。

#### 阶段七：Streamlit 界面 `app.py`（已完成并验收）

**流程**：`浏览器交互 → app.py（页面只调用 RAG 模块）→ 上传 / 重建 / 提问 / 展示`；页面不写核心逻辑，全部通过 `build_index()` 和 `ask()` 两个既有接口驱动。

**页面结构**：

- 侧边栏：`st.file_uploader` 多文件上传（.md / .txt / .pdf）→ "保存到知识库"写入 `data/raw/`；"重建索引"按钮调用 `build_index()` 并展示统计（文档 / chunk / 向量数）；
- 主区：`st.text_input` 问题输入 + "提问"按钮调用 `ask()`；答案 `st.markdown` 展示、token 消耗用 caption、每条检索结果放入 `st.expander`（标题含 `[编号] 来源 · score`，内容为片段原文）；
- 结果存 `st.session_state["result"]`：**Streamlit 每次交互都会从上到下重跑整个脚本**，不存则答案一刷新就丢。

**启动方式**（`streamlit` 命令不在 PATH，统一走模块方式，见运行规范 5）：

```powershell
E:\Anaconda_envs\envs\rag-one\python.exe -X utf8 -m streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`。

**验收结果**：用 Streamlit 官方无头测试 `streamlit.testing.v1.AppTest` 模拟真实点击，24/24 断言 + 上传路径补验通过：

- 首屏结构：标题 / 引导条（未提问时的占位提示）/ 上传控件 / 提问框 / 提问与重建按钮齐全；
- 空输入拦截：点"提问"提示"请先输入问题。"，不报错；
- 提问链路（验收清单 1/2/3）：模拟输入 q01 → 答案"普通员工去上海出差，酒店每晚含税最高可以报销 700 元。使用的资料编号：[1]"、5 个检索折叠区（首条 `[1] 06-travel-policy.md · score=0.6852`）、片段原文可见、token 行显示；提问前后库恒为 10 条（只读链路不触碰索引）；
- 重建按钮：点击提示"完成：10 篇文档 / 10 个 chunk / 集合内 10 条向量"，重建后库仍为 10 条；
- **页面错误不损坏索引（验收清单 4）**：向页面注入"ask 抛异常 / build_index 抛异常"两个故意失败 → 页面显示 `st.error` 提示而非崩溃，库均保持 10 条；
- 上传 → 保存路径补验：AppTest 模拟上传测试文件 → 点"保存到知识库"提示"已保存"、文件真实写入 `data/raw/`（测后已删除，知识库恢复 10 篇）。

#### 收尾：MVP 完成定义核对（规划第 9 节，10/10 达成）

| # | 完成定义 | 核对证据 |
|---|---|---|
| 1 | 一条命令可以建立文档索引 | `python -X utf8 ingest.py`（阶段四） |
| 2 | 一条命令可以启动问答程序 | `python -X utf8 -m src.rag`（命令行）；`python -X utf8 -m streamlit run app.py`（界面） |
| 3 | 能回答知识库内的问题 | q01 端到端实测"700 元 [1]"（阶段六、阶段七 AppTest 双确认） |
| 4 | 每个答案包含来源 | 引用编号 [N] 可逐条追溯，界面折叠区可展开核对（阶段六/七） |
| 5 | 找不到依据时能够拒答 | q24 实测"根据现有资料无法确定"（阶段六） |
| 6 | 能查看 Top-K 原始检索结果 | `src/retriever.py` 逐条打印（阶段五）+ 界面折叠区（阶段七） |
| 7 | 有至少 15 个固定评估问题 | `data/eval/questions.jsonl` 25 题（阶段一） |
| 8 | README 记录安装和运行方式 | 本文件"环境与运行" |
| 9 | README 记录关键参数及其作用 | 本文件"关键参数"（8 项） |
| 10 | 核心流程不依赖 LangChain 或 LangGraph | 全部模块手写，无框架依赖（阶段二~七） |

### v2.0 · 召回与排序（进行中）

#### 阶段一：冻结语料与评估标注（已完成并验收）

**目标**（v2.0 规划第 5 节）：把更新后的语料（9 篇扩写版 Markdown + `10-faq.pdf`）冻结为固定实验语料，评估集扩充到 ≥30 题并补到 chunk 级，为 BM25 / 融合 / 重排的对照实验建立共同基准。

**语料冻结**：新增 `tools/freeze_corpus.py`（运行 `python -X utf8 -m tools.freeze_corpus` 复查），逐文件记录字节数与 SHA256 前 16 位指纹，连同切分参数与实际统计生成 `data/eval/corpus-version.md`——v2.0 全部实验共用的语料版本快照，冻结期内不得新增、重写或替换 `data/raw/` 文件：

```text
文档 10 篇（记录 15 条 = 9 篇 Markdown + PDF 6 页）→ chunk 111 个，平均 717.7 字符
（01 篇 12 块，其余各 11 块）
```

**评估集扩充**：25 → 32 题（q26~q32：关键词 5 / 易混 1 / 语义 1），题型分布：

```text
direct 9 / keyword 5 / multi_source 5 / confusable 4 / unanswerable 3 / reasoning 2 / trap 2 / table 1 / semantic 1
```

配套文档同步：`data/README.md` 与 `data/eval/eval-report.md` 随语料更新同步（32 题、对齐源码切分参数、目标改为 v2.0 阶段六口径），并修正 `questions.jsonl` 中 4 处旧文件名引用（`10-faq.md` → `10-faq.pdf`）。

**chunk 级标注**：31 道可答题标注 `relevant_chunk_ids`（共 103 个“题 × 块”对）；q24（食堂午餐）为空——语料零命中，与拒答答案一致。口径：排除各文档高频复用的模板扩写段（“执行要点 / 常见误区”等），只标含支撑答案的具体陈述的块。

**索引重建**：`python -X utf8 ingest.py` 全量重建（此前库内仍是 v1.0 时期的 10 条旧索引）：

```text
文档数: 10
chunk 数: 111
集合内向量数: 111
```

**验收结果**：临时总验收脚本（独立重算、跑完即删）384/384 断言通过，覆盖规划“阶段一验收清单”8 项：

- 语料：10 份文件可加载，指纹与 `corpus-version.md` 逐一独立重算一致；
- 切分：111 块、平均 717.7 字符、每篇分布吻合；
- 库对齐：库内 id 集合 == 切分结果，111 条文本 / `content_hash` / metadata / 1024 维向量逐条一致；
- 评估集：32 题 id 连续唯一；31 题有来源、31 题有 chunk 标注（均 ≥ 20 要求）；题型含关键词 / 语义 / 多片段 / 拒答四类；
- 检索 smoke：9 类题型各抽 1 题实测（top_k=5），相关块均进入 Top-5：

```text
q01 [direct]        Rank1=06-travel-policy.md:chunk-5  | 相关命中 3/4
q02 [table]         Rank1=10-faq.pdf:page-3:chunk-1   | 相关命中 3/3
q03 [confusable]    Rank1=05-expense-policy.md:chunk-0 | 相关命中 3/4
q04 [reasoning]     Rank1=05-expense-policy.md:chunk-0 | 相关命中 2/4
q11 [multi_source]  Rank1=07-remote-work.md:chunk-0    | 相关命中 4/6
q18 [trap]          Rank1=09-it-support.md:chunk-0     | 相关命中 4/5
q22 [unanswerable]  Rank1=10-faq.pdf:page-1:chunk-0    | 相关命中 1/2
q26 [keyword]       Rank1=09-it-support.md:chunk-2     | 相关命中 2/2
q32 [semantic]      Rank1=10-faq.pdf:page-1:chunk-0    | 相关命中 2/2
```

> 注：“相关命中 X/Y” = 该题 `relevant_chunk_ids` 中进入 Top-5 的数量 / 标注总数；q03 的 Rank1 落在费用报销制度（30 天口径）而非差旅制度（15 天）——confusable 题预期的干扰现象，记为阶段二基线的观察点。

遗留决定：9 题的 `relevant_chunk_ids` 包含 `expected_sources` 之外的来源（FAQ 等冗余覆盖，方向均为“多”）；经复核，`expected_sources` **维持不变**——其语义是“必须命中的来源”，chunk 级公平性由 `relevant_chunk_ids` 保证。

#### 阶段二：v1.0 向量检索基线（已完成并验收）

**目标**（v2.0 规划第 5 节）：在改动检索方案之前，先用当前纯向量链路跑完全部 32 题并锁存结果，作为 BM25 / 融合 / 重排各实验的共同对照。只评估检索，不调用 LLM——生成模型的随机性会掩盖检索问题。

**实现**：新增 `evaluation/` 正式包（与 `src/` 同级、含 `__init__.py`）：

- `evaluation/metrics.py`：指标纯函数（`hit_rank` / `recall_at_k` / `reciprocal_rank` / `relevant_hit_count` / `percentile`），不读文件、不碰网络——后续各检索模式共用同一套公式；
- `evaluation/evaluate_retrieval.py`：评估 CLI，一条命令跑完全部题目并产出两个文件（JSON 机器可读 + Markdown 人类可读）：

```powershell
python -X utf8 -m evaluation.evaluate_retrieval
```

**评估口径**（先定死，避免阶段间漂移）：

- 直接调用生产链路 `src.retriever.retrieve()`，零侵入评估真实链路；
- **题级 Recall**：前 K 命中中含任一相关块记 1，对 31 道有标注题求平均；另记块级覆盖（Top-10 命中块数 / 标注总数）作辅助诊断；
- 检索深度取 `top_k=10`，一次检索同时得到 Recall@5 / Recall@10 与 MRR@10（前 5 是前 10 的前缀）；
- 延迟 = 单题端到端（含查询向量化网络时间），统计全部 32 题（拒答题也真实占用时间）；
- 拒答题（q24）只记录命中内容，不参与 Recall / MRR 统计；
- **防覆盖**：输出文件已存在时直接拒绝运行（`--force` 显式放行）——基线只允许诞生一次，后续实验用各自命名另存（如 `--out data/eval/run-bm25.json`）。

**基线结果**（`data/eval/baseline-v1.json` + `baseline-v1.md`，运行元信息见 JSON `run` 段）：

| 指标 | 值 |
|---|---|
| Recall@5 | 96.8%（30/31） |
| Recall@10 | 100.0% |
| MRR@10 | 0.838 |
| 相关块覆盖（Top-10） | 84.8% |
| 延迟 P50 / P95 | 198 / 574 ms |

分题型：confusable 75.0%（唯一未命中 q20，命中排名 7），其余 8 类均 100%。q20（“外出拜访客户是否占用远程办公天数”）记为本基线观察点，作为后续 BM25 / RRF / Reranker 的对照优化对象。

**验收结果**：临时脚本（独立重算，不复用 `evaluation.metrics`，跑完即删）375/375 断言通过——逐题 5 项指标与 4 项汇总指标和 JSON 全吻合；防覆盖实测（重跑被拒绝、基线文件时间戳不变）；LLM 零调用核查（评估链路无任何生成接口引用）。

**稳定性复跑**（验收清单第 5 条）：换路径重跑全量 32 题，200 项对比指标全一致；3 处差异（q01 / q05 / q15）全部落在 **Top-8~10 近乎并列的块**之间（分数差 < 0.001，score 最大抖动 0.0009），根因是 embedding 服务端浮点抖动——Top-7 以内定序 100% 稳定。「重复运行结果稳定」的本项目口径：**指标级稳定，末位并列块不承诺逐位一致**（已并入决策记录第 11 条）。

#### 阶段三：实现 BM25 检索（已完成并验收）

**目标**（v2.0 规划第 5 节）：手写中文关键词检索链路（chunk → jieba 分词 → 倒排索引 → BM25 Top-N），与向量检索并列作为第二路召回；在冻结语料与同一 32 题评估集上与向量基线对照。

**实现**：三个新文件 + 评估 CLI 扩展（复用 `loaders + splitter` 产出 chunk，与向量索引天然同 id）：

- `src/bm25_store.py`：BM25 核心——`tokenize`（jieba 精确分词：去空白 / 丢纯标点 / 英文小写）、`build_index`（纯函数：chunks + postings 倒排表 + avgdl）、`save_index` / `load_index`（纯 JSON，`lru_cache` 进程内只解析一次）、`search`（查询词去重 → 按倒排累加 → 分数降序 + 同分按 chunk id 升序兜底）；
- `ingest_bm25.py`：BM25 索引入口；
- `tests/test_bm25.py`：首个留在仓库的 pytest（6 用例：空查询 / 未登录词 / 重复词等价 / 同分 tie-break / Top-K 边界 / 结果结构与排序）；
- `evaluation/evaluate_retrieval.py`：`--mode` 增加 `bm25` 分支（`retrieve_by_mode` 分发），评估口径与基线逐条一致。

**打分公式**（第一版经典默认值）：

```text
score(q,d) = Σ IDF(t) · tf·(k1+1) / (tf + k1·(1-b + b·dl/avgdl))
IDF(t) = ln(1 + (N-df+0.5)/(df+0.5))      # Lucene 变体，恒为正、无负分
k1 = 1.5（词频饱和）  b = 0.75（长度归一化）
```

**运行方式**：

```powershell
python -X utf8 ingest_bm25.py                  # 重建（10 篇 → 111 块 / 1515 词项 / 平均 326.3 tokens）
python -X utf8 -m src.bm25_store                # 演示检索
python -X utf8 -m pytest tests/test_bm25.py -v  # 单元测试（6 用例）
python -X utf8 -m evaluation.evaluate_retrieval --mode bm25 --out data/eval/run-bm25.json
```

**BM25 结果**（`data/eval/run-bm25.json` + `run-bm25.md`）：

| 指标 | BM25 | 向量基线 | 差值 |
|---|---:|---:|---:|
| Recall@5 | 100.0% | 96.8% | +3.2pp |
| Recall@10 | 100.0% | 100.0% | — |
| MRR@10 | 0.888 | 0.838 | +0.050 |
| 相关块覆盖（Top-10） | 93.3% | 84.8% | +8.5pp |
| 延迟 P50 / P95 | 0 / 1 ms | 198 / 574 ms | 纯内存，无网络调用 |

**对照分析**（逐题与分题型完整数据见 run-bm25.md）：

- 向量基线唯一短板 **q20 修复：首个相关块 rank 7 → 3**；direct 类 9 题全部 rank 1（MRR 0.778 → 1.000）；
- BM25 弱项符合预期：**q32 语义题 rank 2 → 5**（“台风 / 地铁停运”无词面匹配，靠泛词进 Top-5）；multi_source MRR 0.867 → 0.800；
- 干扰模式：`10-faq.pdf:page-1:chunk-0`（FAQ 汇总块，主题词堆叠）在 BM25 中霸榜；各文档模板扩写段（chunk-9 系列）成批涌入 Top-10——词面重复敏感是 BM25 的固有偏差；
- 两路互补：共同命中相关块 81 个，向量独有检出 2 个、BM25 独有检出 11 个——RRF 融合的输入已就位；
- 延迟口径：P50/P95 为稳态值；首题含 jieba 词典一次性加载（843ms），会把 avg 拉到 26.5ms。

**验收结果**：临时脚本（独立重算，跑完即删）两组全绿——512/512（索引侧：id 三方对齐 / tokens 与 postings 全表重算 / 打分公式独立复算 / 可重建性 / 边界）+ 252/252（产物侧：逐题指标重算 / 与函数级结果交叉一致 / 语料指纹十文件复核）；pytest 6/6。验收中发现并处理三件事：评估 CLI 的 `--mode` 校验未放开 bm25（按讲义补齐）、`.gitignore` 缺 `storage/bm25/`（已补，索引不提交）、`03-attendance.md` 在基线生成后被改动 1 行导致 Chroma 与当前语料不同步（恢复提交版 + 重建 BM25 后三方对齐，详见决策 17）。

#### 阶段四：实现混合检索与 RRF 融合（已完成并验收）

**目标**（v2.0 规划第 5 节）：向量相似度与 BM25 分数不在同一量纲，不能直接加权相加；改用 **RRF（Reciprocal Rank Fusion）** 只依赖排名做融合——`RRF(d) = Σ 1/(k + rank_i(d))`，初始配置 `vector_candidates=20 / bm25_candidates=20 / rrf_k=60`；在同一评估集上完成 vector / bm25 / hybrid 三组全量对比。

**实现**：三个新文件 + 评估 CLI 扩展（融合层为纯函数，零新增依赖）：

- `src/fusion.py`：RRF 核心——`rrf_fuse(rank_lists, top_k=10, k=RRF_K)`，按 chunk id 去重合并，每条命中累加各路的 `1/(k+rank)`；每路原始排名与分数原样保留（键名按路名动态生成：`vector_rank / vector_score / bm25_rank / bm25_score`），未命中该路的条目显式补 `None`；同分按 chunk id 升序兜底（与 BM25 一致）；
- `src/hybrid_retriever.py`：双路召回 + 融合——`hybrid_search(question, top_k=10)` = 向量 Top-20 + BM25 Top-20 → `rrf_fuse`；`format_fused` 展示每条命中的两路名次（`—` 表示仅单路命中）；
- `tests/test_fusion.py`：融合单元测试（6 用例：去重合并 / 单路保留 / 共识胜单路 / 同分兜底 / 分数可复算+截断 / 空输入边界）；
- `evaluation/evaluate_retrieval.py`：`--mode` 增加 `hybrid` 分支；产物每条命中附 `vector_rank / bm25_rank`（条件字段，向后兼容）。

**融合公式**（k=60 为平滑常数：压平头部名次优势、倾向“两路共识”）：

```text
RRF(d) = Σ_i 1 / (k + rank_i(d))     # i 遍历各检索路；未命中该路不贡献分数
k = 60     # 1/61 + 1/65 ≈ 0.0318（两路中等）恒大于 1/61 ≈ 0.0164（单路称王）
```

融合输出条数：本阶段评估口径与基线一致，融合后取 Top-10；规划初始配置中的 `fused_candidates=20`（融合后保留的候选池）服务于阶段五 Reranker 的输入——届时以 `top_k=20` 调用融合函数即可，融合层无需改动。

**运行方式**：

```powershell
python -X utf8 -m src.hybrid_retriever             # 演示：3 题的两路名次与融合过程
python -X utf8 -m pytest tests/test_fusion.py -v    # 单元测试（6 用例）
python -X utf8 -m evaluation.evaluate_retrieval --mode hybrid --out data/eval/run-hybrid.json
```

**Hybrid 结果**（`data/eval/run-hybrid.json` + `run-hybrid.md`，与两条单路同口径）：

| 指标 | Hybrid | BM25 | 向量基线 |
|---|---:|---:|---:|
| Recall@5 | 100.0% | 100.0% | 96.8% |
| Recall@10 | 100.0% | 100.0% | 100.0% |
| MRR@10 | 0.925 | 0.888 | 0.838 |
| 相关块覆盖（Top-10） | 91.7% | 93.3% | 84.8% |
| 延迟 P50 / P95 | 195 / 458 ms | 0 / 1 ms | 198 / 574 ms |

非满分题：q03（rank 2）、q16（rank 3）、q20（rank 3）、q32（rank 2），其余 27 题首个相关块均为 rank 1。

**对照分析**（逐题数据见 run-hybrid.md）：

- 三组汇总：R@5 `96.8% → 100% → 100%`、MRR `0.838 → 0.888 → 0.925`、覆盖 `84.8% → 93.3% → 91.7%`（向量 / BM25 / hybrid）——融合把两路短板一起修复，MRR 为三组最高；
- 相对向量路：**改善 6 题、零退化**——q20（7 → 3，验证 D3 开工前推演）、q01 / q06 / q14 / q21 / q31（2 → 1）；
- 相对 BM25 路：改善 4 题（q23 / q25 / q26 的 2 → 1、q32 的 5 → 2）；**退化 2 题**——q03（1 → 2）、q16（2 → 3），首个相关块均仍在 Top-3、R@5 无损，机制为“BM25 独占首名被两路共识块反超”，其中 q16 是凸性反超的纯数学案例（详见附录知识笔记 D4）；
- 覆盖 91.7% 介于两路之间：融合结果中少量相关块被“两路都有但非相关”的共识块挤出 Top-10——阶段五 Reranker 的观察点。

**验收结果**：临时脚本（独立重算，跑完即删）**2149/2149 硬断言通过**——产物自洽（32 题 × 10 条逐条重算字段 / 去重 / 排序 / 分数 / 指标 / 汇总 / 延迟）、与 BM25 产物全量交叉一致、手算账本（q01 / q20）逐位吻合、十文件语料指纹复核（延续字节级纪律）；pytest 12/12（融合 6 + BM25 6）。两项口径发现：① 向量侧跨时段对照有漂移——探针实测同深重跑 3/3 逐位稳定、产物生成时刻状态可现场复现，差异源于基线记录时段与本次运行的服务状态差（口径已并入决策 11）；② 产物 score 序列化时已 round 4 位（q01 前两名 0.0320184 / 0.0320020 显示同为 0.032），复现排序必须按完整精度重算、不能用显示分数做 tie-break。

#### 阶段五：接入 Reranker（已完成并验收）

**目标**（v2.0 规划第 5 节）：召回负责“尽量不要漏”，重排负责“把最有用的排到前面”——混合召回 Top-20 → question/chunk 成对评分 → 重排 → Top-5 进 Prompt。选型 `BAAI/bge-reranker-v2-m3`（与 bge-m3 同家族的交叉编码模型，硅基流动 Rerank API 提供）；rerank 不在 OpenAI 端点集内，用 `httpx` 直连 `{base_url}/rerank`（httpx 是 openai SDK 的底层依赖，按“直接 import 就显式声明”写入 requirements）。

**实现**：两个新源文件 + 一个测试文件 + 评估 CLI 扩展（融合层与既有模块零改动）：

- `src/reranker.py`：供应商封装——`rerank(question, candidates, top_k)` 用 `top_n=len(texts)` 拿回全部候选分数、在本地排序截断；`RerankError` 不吞错；空候选短路不发请求（实测 API 对空列表报 400）；`last_usage()` 暴露最近一次调用的 token 用量；
- `src/hybrid_reranker.py`：组合层——`hybrid_rerank_search(question, top_k=5, candidate_k=20, fallback=True)`，先逐条记 `rrf_rank`（重排前名次）再重排（`rank` 重写为最终名次）；API 失败时回退融合 Top-K 并打印 `[WARN]`（`fallback=False` 则严格抛错）；
- `tests/test_reranker.py`：重排链路单元测试（9 用例：重排字段与顺序 / 同分稳定 / 截断 / 候选不足 / 空候选短路 / API 失败抛错 / rrf_rank 留档 / 回退 / 严格模式），全程 mock、零网络；
- `evaluation/evaluate_retrieval.py`：`--mode` 增加 `hybrid_rerank` 分支；产物每条命中附 `rrf_rank / rerank_score`（条件字段，向后兼容）；`src/config.py` + `RERANK_MODEL`、`.env.example` 同步。

**运行方式**：

```powershell
python -X utf8 -m src.reranker              # 演示：打分与 token 用量
python -X utf8 -m src.hybrid_reranker       # 演示：3 题的重排前后名次
python -X utf8 -m pytest tests/ -v          # 单元测试（21 用例 = BM25 6 + 融合 6 + 重排 9）
python -X utf8 -m evaluation.evaluate_retrieval --mode hybrid_rerank --out data/eval/run-hybrid-rerank.json
```

**Rerank 结果**（`data/eval/run-hybrid-rerank.json` + `run-hybrid-rerank.md`，四组同口径）：

| 指标 | hybrid_rerank | hybrid | BM25 | 向量基线 |
|---|---:|---:|---:|---:|
| Recall@5 | 100.0% | 100.0% | 100.0% | 96.8% |
| Recall@10 | 100.0% | 100.0% | 100.0% | 100.0% |
| MRR@10 | **1.000** | 0.925 | 0.888 | 0.838 |
| 相关块覆盖（Top-10） | **94.8%** | 91.7% | 93.3% | 84.8% |
| 延迟 P50 / P95 | 954 / 2057 ms | 195 / 458 ms | 0 / 1 ms | 198 / 574 ms |

31 道计分题的**首个相关块全部为 rank 1**（hybrid 时 4 题非 rank 1：q03 / q16 / q20 / q32）。

**对照分析**（hybrid → hybrid_rerank，逐题数据见 run-hybrid-rerank.md）：

- **hybrid 的四个遗留问题全部修复**：q03（2 → 1，共识妥协）、q16（3 → 1，凸性反超）、q20（3 → 1，向量弱）、q32（2 → 1，BM25 弱）；31 题中 20 题的 rank 1 被重排调整过，其中 2 题从融合第 10 / 11 位直接抬到首位；
- 覆盖 91.7% → 94.8%：净增 q01（3 → 4）、q22（1 → 2）、q23（3 → 4）、q25（3 → 4）；唯一微降 q18（5 → 4）——被挤出的是原 hybrid 第 10 位边缘块，hit_rank 与 Top-5 覆盖不受影响；
- **成本账**：每题一次重排调用（20 候选 ≈ 8.1k input tokens、P50 +约 760ms）——以“每题多 0.76 秒”换 MRR +0.075、覆盖 +3.1pp、四个遗留问题清零；
- **重排分即相关性量级**：rank 1 重排分 0.9+ 的相关块与 0.0~0.6 的非相关块彻底分层（hybrid 的 RRF 分全部挤在 0.03 一带）；拒答题 q24 的 rank 1 仅 0.0151（其余计分题 rank 1 均 ≥ 0.13）——低分与“无强相关块”高度吻合，可作拒答信号的观察点（阶段七）；
- 修复机制的逐题账本见附录知识笔记 D5。

**验收结果**：本阶段由助手按定稿讲义实施并自检——pytest 21/21（重排 9 用例全程离线）；`src.reranker` 演示真相关块 rank 2 → 1（rerank=0.9826，token 用量 109）；`src.hybrid_reranker` 演示 3 题名次全部归位；全量评估 32 题（MRR@10 = 1.000）+ 与 `run-hybrid.json` 逐题对照 + 回退审计（32 题全部带 `rerank_score`，零回退、零 `[WARN]`——32 次 API 调用全部成功）。

#### 阶段六：端到端对照实验（已完成并验收）

**目标**（v2.0 规划第 5 节）：E1~E4 四方案已在阶段四 / 五以完全同口径完成检索层对照（四份 `run-*` 产物）；本阶段对其中表现稳定的 **E1（vector）与 E4（hybrid_rerank）** 补上端到端答案评估——同一 32 题走「检索 → 生成」全链路，逐题记录：正确片段是否进 Top-5、答案是否正确、引用是否真正支撑、有无无依据内容、Prompt token 数与检索 / 重排 / 生成三段延迟，并对照成功标准（Recall@5 ≥ 85%、答案正确率 ≥ 80%、引用准确率 ≥ 90%、拒答准确率 ≥ 90%）。

**实现**：一个端到端评估脚本 + 一轮人工判定，`src/` 零改动（全部复用 retrieve / hybrid_search / rerank / generate_answer 原函数）：

- `evaluation/evaluate_e2e.py`：`--mode vector|hybrid_rerank` 对应 E1 / E4 两条链路；E1 记 retrieve + generate；E4 在脚本内按 `hybrid_reranker` 组合层同一逻辑组装，把**融合（双路召回 + RRF）与精排分开计时**（产品链路是一体的两段，评估时拆开记账）；重排失败按回退口径记 `rerank_fallback`；生成 token 取 `resp.usage`，重排 token 取 `last_usage()`；产物沿用 `run-*` 结构（含逐题答案全文与引用编号），防覆盖与 `--limit` 调试与检索评估一致；
- 判定环节：以临时脚本导出「答案引用编号 → 引用块原文」逐条核对（53 个引用块清单，跑完即删），按定稿口径（见决策 20）填写 `data/eval/eval-report.md`——32 题 × 4 判定列 × 双链路。

**运行方式**：

```powershell
python -X utf8 -m evaluation.evaluate_e2e --mode vector         --out data/eval/run-e2e-vector.json
python -X utf8 -m evaluation.evaluate_e2e --mode hybrid_rerank  --out data/eval/run-e2e-hybrid_rerank.json
```

**端到端结果**（`run-e2e-vector.*` / `run-e2e-hybrid_rerank.*`，质量指标）：

| 指标 | E1 vector | E4 hybrid_rerank | 成功标准 | 达标情况 |
|---|---:|---:|---:|---|
| Recall@5（chunk 级，端到端） | 96.8%（30/31） | 100%（31/31） | ≥ 85% | 均达标 |
| 答案正确率 | 93.8%（30/32） | 100%（32/32） | ≥ 80% | 均达标 |
| 引用准确率（严格口径） | 62.1%（18/29） | 79.3%（23/29） | ≥ 90% | 均未达标 |
| 拒答准确率 | 100%（3/3） | 100%（3/3） | ≥ 90% | 均达标 |
| 幻觉数 | 0 | 0 | — | — |

| 运行观测 | E1 | E4 |
|---|---:|---:|
| Prompt tokens（avg） | 2368 | 2425 |
| Completion tokens（avg） | 44 | 53 |
| 召回段延迟 P50 | 310 ms（retrieve） | 192 ms（fuse） |
| 精排段延迟 P50 | — | 755 ms |
| 生成段延迟 P50 | 2202 ms | 2496 ms |
| 总延迟 P50 / P95 | 3204 / 8037 ms | 3705 / 7817 ms |
| 重排 tokens（avg / P50） | — | 9401 / 9580 |
| 重排回退次数 | — | 0 |

**对照分析**：

- **端到端 R@5 与检索层完全一致**（E1 96.8% / E4 100%）：Top-5 直达 Prompt 无中间损耗；E1 唯一未命中题 q20 直接传导为产出层缺陷——检索不到外勤块 → 生成端误拒答 + 4 条引用零支撑，一题三失；
- **E4 相对 E1 全面胜出**：答案正确率 93.8% → 100%、引用准确率 62.1% → 79.3%、Top-5 覆盖 70.9% → 91.6%；E1 的两例误拒答（q12 / q20）在 E4 全部修复；
- **误拒答的两种机理**（E1）：q20 是检索缺陷传导（Top-5 无依据块）；q12 是 Top-5 里有「不能跨周累计」原文仍答「无法确定」（生成端退化）——检索质量是根因层，仅优化生成端不足以补齐，与阶段五「把决定前排的权力交给能读原文的一层」的结论一致；
- **引用准确率双链路均未达 90% 目标**：错误模式集中且一致——「多标编号」：答案把 Top-5 中无关的模板块 / 其他主题块一并标入引用（与决策 15 的相似模板段直接相关——hard negative 在引用层同样制造干扰）；Rerank 把正式区块排前使引用精度显著改善（+17.2pp）但未治本，严格口径如实记录，作为阶段七界面观察项；
- **拒答与成本账**：q22~q24 双链路全部正确拒答、零编造；E4 每题比 E1 多付约 0.95s（fuse + rerank P50），换来答案 +6.2pp、引用 +17.2pp、覆盖 +20.7pp。

**验收结果**：本阶段由助手实施并自检——独立重算验收（不依赖评估包汇总逻辑，从产物 JSON 原始字段重推导：recall 与 token 均值同产物 summary 完全一致；引用编号去重口径 56 / 72 与判定分母一致）；抽检 q12 / q20 / q32 双链路答案与判定记录一致；`eval-report.md` 完成 32 题 × 4 判定列双链路填写（含运行观测、检索层与端到端对照、失败案例与数据观察）。

---

## 附录

> 与各版本（v1.0 / v2.0）开发阶段平行的独立记录线，内部分两条子线，性质不同、分开归档：
>
> - **调优实验**（编号 T1、T2……）：凡「改一个参数 → 重建索引 → 用固定评估集对比效果」的对比实验（T1 时为 25 题，v2.0 起为 32 题）。本板块保留“为什么是这个值”的完整证据链；「关键参数」表只反映当前生效值。
> - **知识笔记**（不占 T 编号、非实验）：开发中实测沉淀的 API / 协议结构、评估指标口径等知识。

### 调优实验

#### T1 · CHUNK_SIZE：800 → 400（重叠 150 不变）

**动机与假设**：块更小 → 问题向量与目标段落更贴合，预期检索更准、上下文更省 token；风险是语义单元被切断。当前 10 篇手册均为 663~783 字符的短文，800 等于“每篇整切”，400 会把每篇切成 3~4 块。

**操作要点**（改切分参数必须重建索引才生效：参数只在 ingest 时读取，库里存的是旧切分的向量）：

```powershell
# 1) 改 src/splitter.py: CHUNK_SIZE = 400（第一轮只动这一个变量，OVERLAP 不动）
# 2) 全量重建（build_index 走 reset_collection 先删后建，不残留旧数据）
python -X utf8 ingest.py
# 3) 对比检索效果
python -X utf8 -m src.retriever
```

**数据**（同一知识库、同一 25 题评估集、top_k=5）：

| 配置 | chunk 数 | 来源级 Recall@5 | q01 Rank1 |
|---|---|---|---|
| 800 / 150（基线） | 10 | 31/31 = 100% | 06-travel-policy.md |
| 400 / 150（实验） | 32 | 29/31 = 93.5% | 10-faq.md |

**观察**：

- 细切后召回率不升反降：短文手册的“一篇 = 一个完整语义单元”在 800 整切下天然保留；400 切碎后单块语义不完整，与问题向量的匹配反而变弱；
- q01 首位命中从《差旅制度》滑到《FAQ》：FAQ 恰有“上海酒店都是每晚最多 700 元吗”同主题段落，块变碎后两类文本的距离被拉近；
- 代价：chunk 数 10 → 32，top-5 容易被同一篇的相邻块挤占，来源覆盖面变窄；重叠 150 占 400 的 37.5%，同篇相邻块同时命中时上下文重复率高（若长期用 400，OVERLAP 应降到 60~80）。

**结论**：当前短文知识库下维持 800/150；将来加入长文档（PDF 手册）后值得重开一轮。

**当前状态**：两轮实验均已闭环。第一轮为阶段五验收期间的临时切换（测后恢复 800）；第二轮为阶段五之后再次手动设为 400 并重建（库内实测 32 条：10 个 chunk-0、22 个后续块）。阶段六开工时发现该漂移，经确认后**已恢复 800/150 并重建索引**（库内实测 10 条、每篇 1 块），源码与库一致——「关键参数」表已按“只反映当前生效值”同步为 800。

### 知识笔记

#### D1 · ChatCompletion 返回结构（阶段六 generator 实测）

**背景**：`generator.py` 调用 `_get_client().chat.completions.create(...)` 后拿到的 `resp`，是 OpenAI 兼容协议的标准返回对象 `ChatCompletion`（SDK 里的 Pydantic 模型）。用临时脚本发了一次最小请求（Qwen3-8B、“只回复两个字：收到”、temperature 0.2，脚本跑完即删），真实返回节选：

```json
{
  "id": "01a0d7a4db0387ff076f6685529ef08f",
  "object": "chat.completion",
  "model": "Qwen/Qwen3-8B",
  "created": 1790324300,
  "choices": [
    {
      "index": 0,
      "finish_reason": "stop",
      "message": {
        "role": "assistant",
        "content": "收到",
        "tool_calls": null,
        "refusal": null,
        "annotations": null
      }
    }
  ],
  "usage": {
    "prompt_tokens": 18,
    "completion_tokens": 1,
    "total_tokens": 19,
    "prompt_cache_hit_tokens": 0,
    "prompt_cache_miss_tokens": 18
  }
}
```

**分区导览**：

| 区域 | 关键字段 | 含义 | 本项目取用 |
|---|---|---|---|
| choices（拿答案） | `choices[0].message.content` | 答案正文 | `generate_answer` 直接取用并 strip |
| | `choices[0].message.role` | 恒为 `assistant` | 阶段七多轮时转抄回 messages |
| | `choices[0].finish_reason` | 停笔原因：`stop`（自然说完）/ `length`（撞 max_tokens 被截断）/ `tool_calls` / `content_filter` | MVP 不检查；生产必查 `length`，截断答案不可直接用 |
| usage（算账） | `prompt_tokens` / `completion_tokens` / `total_tokens` | 输入 / 输出 / 总 token 数，计费依据 | 转抄进 `generate_answer` 返回值 |
| 快递单据 | `id` / `created` / `model` / `object` | 请求 ID、时间戳、实际模型、对象类型 | 不用 |
| 空槽位 | `logprobs` / `refusal` / `tool_calls` / `audio` 等 = `null` | 协议为可选功能预留的字段位，功能没开就是 null | 见 null 即“功能未开”，直接跳过 |

**要点**：

1. **choices 是列表的原因**：协议支持一次采样 `n` 个候选回答（默认 `n=1`），故永远取 `[0]`——与 Chroma `query()` 返回“外层 = 查询数、内层 = K 条”的双层嵌套是同一设计哲学：协议支持批量，你只用了 1。
2. **token 账单的量级直觉**：RAG 一次问答中 prompt（5 个 chunk ≈ 3500 字）通常远大于 completion（几百 token）——省钱方向是少喂上下文（top_k / chunk 大小），而不是让模型少说。硅基流动附带的 `prompt_cache_hit/miss_tokens` 为 Qwen 上下文缓存计费字段：多轮对话中 system + 历史这类固定前缀命中缓存更便宜。
3. **assistant 消息的出生地**：`resp.choices[0].message`（role + content 俱全）就是 assistant 消息本体；请求侧 messages 里出现的 `{"role": "assistant", ...}` 是把上一轮的它转抄回来——同一东西的“出生证明”与“存档”。这是阶段七 `chat.py` 多轮组装的地基；单轮问答（当前 generator）只有一条 user 消息，不需要任何 assistant 历史。
4. **SDK 返回模型字段固定**：没用的功能不会从返回里消失（位子永远在），一排 null 是“协议在场、功能未开”，不是错误。

#### D2 · MRR 平均倒数排名：定义与实测账本（v2.0 阶段三）

**背景**：v2.0 的检索评估（向量基线 / BM25 / 后续 RRF）统一用 MRR@10 衡量“排序质量”——指标实现见 `evaluation/metrics.py`，评估口径见「工作记录 → v2.0 → 阶段二」。这里沉淀概念定义与实测账本（数字为 2026-09-27 对 `run-bm25.json` / `baseline-v1.json` 的实查复算）。

**定义**：

```text
RR（Reciprocal Rank，倒数排名）= 1 ÷ 首个相关块在结果中的排名
MRR@10 = 全部可答题 RR 的平均值（排名深度截断在前 10，10 名之外记 0）

排名 1 → RR = 1.000     排名 2 → RR = 0.500     排名 3 → RR = 0.333
排名 5 → RR = 0.200     前 10 无相关块 → RR = 0
```

**实测账本**（BM25 / 31 道可答题）：25 题首个相关块排第 1（RR = 1.000），6 题非满分：

| 题 | 类型 | 首个相关块排名 | RR |
|---|---|---:|---:|
| q16 | multi_source | 2 | 0.500 |
| q20 | confusable | 3 | 0.333 |
| q23 | unanswerable | 2 | 0.500 |
| q25 | multi_source | 2 | 0.500 |
| q26 | keyword | 2 | 0.500 |
| q32 | semantic | 5 | 0.200 |

```text
MRR = (25 × 1.000 + 0.500 + 0.333 + 0.500 + 0.500 + 0.500 + 0.200) ÷ 31
    = 27.533 ÷ 31 ≈ 0.888
```

**要点**：

1. **三个指标各管一段**：Recall@K 管“找没找到”（首个相关块进前 K 就记 1，不看位置）；相关块覆盖管“找到了多少”（命中块数 ÷ 标注总数）；MRR 管“排得靠不靠前”。q32 是活例：首个相关块第 5 名——Recall@5 仍算命中，RR 只拿 0.200。
2. **0.888 的直觉**：RR 是名次的倒数，MRR ≈ “1 ÷ 首个相关块的平均名次”。BM25 0.888 ≈ 平均第 1.13 名（满分 25/31）；向量基线 0.838 ≈ 平均第 1.19 名（满分 22/31）。两路差距主要来自满分题数与 q20 的名次（7 → 3）。
3. **为什么在意排序**：RAG 把 Top-K 按顺序喂进 Prompt，越靠前的块越容易被模型引用；把某题首个相关块从第 5 名提到第 1 名，召回指标不变、该题 RR 从 0.200 升到 1.000——这类“名次前移”正是阶段四 RRF 的优化方向之一。
4. **MRR 只适用于有标准答案的评估**：拒答题（q24）与未标注题不参与统计；真实提问没有标准答案，不能用 MRR 判断是否该拒答——拒答是生成端 Prompt 的职责（阶段六）。

#### D3 · RRF 与 Rerank：概念边界与 q20 共识复算（v2.0 阶段四开工前）

**背景**：v2.0 阶段三验收后，围绕 RRF 与 rerank 连续追问（「RRF 是什么」「BM25 是 RRF 吗」「RRF 就是 rerank 吗」「直接 rerank 不就好了吗」「rerank 是模型吗」）。此处把 BM25 / RRF / Reranker 三个易混概念的边界定死；q20 数字为对 `baseline-v1.json` / `run-bm25.json` 的实查 + k=60 公式推演（阶段四实测复核）。

**三个概念的定位**：

| 概念 | 性质 | 输入 → 输出 | 链路位置 |
|---|---|---|---|
| BM25 | 检索打分算法（tf / idf / 长度归一化） | 查询词 + 单篇文档 → 分数 | 第二路召回（阶段三已实现） |
| RRF | **融合**算法（纯算术、无模型、免参数） | 多条已排名的列表 → 一条融合排名 | 融合层（阶段四） |
| Reranker | **重排**模型（默认指交叉编码器） | 一条候选列表 + 问题 → 逐条相关性打分 | 精排层（阶段五） |

**边界一 · BM25 ≠ RRF**：BM25 是“一名选手”（产出一条候选排名），RRF 是“计分规则”（把多路排名合到一起）。RRF 公式 `Σ 1/(k + rank_i(d))`（k 默认 60）只看名次、不看分数——这正是绕开“余弦相似度与 BM25 分数不同量纲不能相加”的方式（规划第 240-246 行）。

**边界二 · RRF ≠ Rerank**：RRF 回答“两路怎么合并成一条”（**集合问题**）；rerank 回答“一条列表里谁排最前”（**排序问题**）。rerank 的输入是“一条列表”，它不会自己跑两路检索——**合并器是双路召回的必需品，rerank 是可选增强**。四种模式里 `hybrid`（止于 RRF）与 `hybrid_rerank` 的差别就是这一步。“跳过 RRF 直接 rerank”实际只有两种写法：两路 concat 后全量 rerank（成本翻倍，且 reranker 逐条打分看不见“两路共识”这个信号），或先挑 20 条再 rerank（怎么挑又回到合并问题，RRF 就是那个免参数的挑法）。RRF 的四样独立价值：① 零成本把候选 40 → 20（贵组件只碰压小后的候选集）；② 多路共识加成（见下）；③ 降级档位——阶段五验收清单要求“API 失败回退 hybrid”，hybrid 就是 RRF 的产物；④ 实验归因——E3 的 Recall 管融合、E4 的 MRR 管重排，两笔账分开算。

**边界三 · Rerank 的实现是模型（交叉编码器）**：把“问题 + chunk”拼成一整段送进模型（`[CLS] 问题 [SEP] chunk [SEP] → 相关性分数`），注意力层里问题与 chunk 逐词交互——精度高，但每对 (问题, chunk) 必须现场推理、不能预计算，只能处理少量候选。与召回用的**双塔（Bi-Encoder）**的分工：

| | 双塔（召回，bge-m3） | 交叉编码器（重排） |
|---|---|---|
| 编码方式 | 问题、文档分开编码 | 问题与文档拼接后一起编码 |
| 能否预计算 | 能（文档向量离线建索引） | 不能（逐对现场推理） |
| 速度 | 快，可扫全库 | 慢，只处理几十条 |
| 职责 | “别漏” | “排准” |

其他实现（LLM 逐条打分、规则加权）存在，但非 Reranker 一词的默认所指。项目先定与供应商无关的接口 `rerank(question, candidates, top_k)`（规划第 3 节），本地模型（如 BGE-reranker-v2-m3）或 API 在阶段五接入时确认。

**q20 共识复算**（k=60，两路各 Top-20 取候选）：q20 两个相关块在两路中的实际排名（对两份评估产物实查）：

```text
              向量路    BM25 路
chunk-1       rank 7    rank 4
chunk-7       rank 9    rank 3
```

```text
chunk-1: 1/(60+7) + 1/(60+4) = 1/67 + 1/64 ≈ 0.031
chunk-7: 1/(60+9) + 1/(60+3) = 1/69 + 1/63 ≈ 0.030
对照（单路 rank-1 的块）:      1/(60+1)      ≈ 0.016
```

两个共识块的融合分接近单路 rank-1 的两倍——阶段四实测预期：q20（向量基线唯一短板）的相关块将被推回 Top-5。即 RRF 的“共识统治”：两路任意名次的两个倒数和，恒大于只在单路称王的块。

#### D4 · RRF 实测账本：q20 共识修复与 q16 凸性反超（v2.0 阶段四）

**背景**：阶段四混合检索上线后，对 `run-hybrid.json` 做了独立重算与两路交叉验收；这里沉淀两个互为镜像的实测账本——一个是 RRF 想要的“共识统治”（q20），一个是它顺带暴露的“凸性反超”（q16）。数字均为对产物 JSON 的实查复算。

**账本一 · q20 共识修复（D3 开工前推演已由实测验证）**：两个相关块在两路中的名次（chunk-1 v7 / b4、chunk-7 v9 / b3）经 `Σ 1/(60+rank)` 融合后双双进入 Top-10，首个相关块 rank 7 → 3（产物节选）：

```text
rank3  03-attendance.md:chunk-1   1/67 + 1/64 = 0.0306   ← 相关块（v7 / b4）
rank7  03-attendance.md:chunk-7   1/69 + 1/63 = 0.0304   ← 相关块（v9 / b3）
```

对照单路 rank-1 的 `1/61 ≈ 0.0164`——两路任意名次的两个倒数和，恒大于只在单路称王的块。

**账本二 · q16 凸性反超（三个候选的两路名次和全为 6）**：

```text
候选（融合排名）                 向量路  BM25 路   RRF 分
08-information-security:chunk-1     1      5      1/61 + 1/65 = 0.0317781
09-it-support:chunk-1               2      4      1/62 + 1/64 = 0.0317540
09-it-support:chunk-0（相关）       3      3      1/63 + 1/63 = 0.0317460   ← 垫底
```

相关块在 BM25 下 rank 2、融合后 rank 3（“相对 BM25 退化”两题之一，另一题 q03 为 1 → 2）。机制：`1/(k+r)` 对 r 是**凸函数**——名次和固定时，两路名次越不均匀的组合得分越高（`1/62 + 1/64 > 2/63`）；k=60 把头部差距压平后，1e-5 量级的差值即决定近并列区排序。

**要点**：

1. **同和看凸性、异和看总和**：解读融合相对单路的名次变化前，先按“两路名次和”分组——和更小的（共识更深）自然获胜；和相同的组内才会发生凸性反超。q16 三个候选和全为 6，属纯凸性案例，不是融合 bug。
2. **凸性不能靠调 k 消除**：k 越小越偏向单路头部、越大越趋于稳定共识，凸性都在；若必须保护“双路对称”的共识块，应在融合后加精排（Reranker，阶段五）或引入加权——属后续阶段观察项，本阶段不修实现。

#### D5 · Reranker 修复账本：三组“粗打分失手、精排归位”的实测（v2.0 阶段五）

**背景**：混合检索的四个非满分题（q03 / q16 / q20 / q32）在接入重排后全部修复为 rank 1。这里沉淀三组互为补充的实测账本，说明“为什么精排能修好粗打分修不好的排序”。数字均为对两份产物 JSON 的实查复算。

**账本一 · q16 凸性反超组（D4 的镜像后续）**：D4 记录过“三个候选两路名次和全为 6、纯凸性分胜负”，相关块的 `(v3, b3)` 组合垫底。重排后结局反转：

```text
q16 重排实测（同一批候选，rr = 重排分）
07-remote-work.md:chunk-7（相关）           rr=0.9687  ← rrf 第 4 → 第 1
08-information-security.md:chunk-0（相关）  rr=0.9171  ← rrf 第 6 → 第 2
08-information-security.md:chunk-1（非相关）rr=0.8358  ← rrf 第 1 → 第 3
09-it-support.md:chunk-0（相关）            rr=0.7665  ← rrf 第 3 → 第 4
09-it-support.md:chunk-1（非相关）          掉出 Top-5 ← rrf 第 2
```

D4 里“名次和相同、融合分差 1e-5”的三个候选，被重排用 0.97 / 0.92 / 0.84 彻底拉开——**融合看不见的“真假共识”，逐对读原文能看见**。

**账本二 · q03 共识妥协组**：RRF 首名被“两路都有但非相关”的 `05-expense-policy.md:chunk-0`（v1 / b4）占据（相关块只排到 2~4）。重排后：

```text
06-travel-policy.md:chunk-7（相关）    rr=0.9474  ← rrf 第 4 → 第 1
06-travel-policy.md:chunk-0（相关）    rr=0.9371  ← rrf 第 2 → 第 2
10-faq.pdf:page-3:chunk-0（相关）      rr=0.9313  ← rrf 第 6 → 第 3
05-expense-policy.md:chunk-0（非相关） rr=0.6147  ← rrf 第 1 → 第 5
```

非相关共识块与相关块的 RRF 分在产物里显示同为 0.032（差异在 4 位小数之后，序列化口径见决策 11），重排后拉开到 0.9474 vs 0.6147——量级差来自“读没读懂问题”，不是名次算术。

**账本三 · 召回弱者补位（q20 / q32）**：向量弱题 q20 的相关块 `chunk-1`（rrf 第 3）重排分 0.9882 升至第 1、`chunk-7`（rrf 第 7）升至第 3；BM25 弱题 q32 的 `chunk-4`（rrf 第 4，rr=0.2125）也升至第 1——q32 前 3 名重排分整体偏低（0.21 / 0.07 / 0.06），语义题在重排模型眼里也“不够像”，但相对序正确。

**要点**：

1. **重排分与相关性同量级、RRF 分与相关性不同量级**：RRF 分只编码“两路名次算术”（候选全体挤在 0.028~0.033），重排分编码“问题与原文的逐词关系”（0.0~0.99）——两级打分工序互补，正是“宽召回 + 窄精排”的收益来源；
2. **凸性反超 / 共识妥协都是粗打分的系统性现象，不是 bug**：修法不是调 k 或改融合，而是把“决定前排”的权力交给能读原文的一层；
3. **低分可作拒答信号（观察项）**：拒答题 q24 的 rank 1 仅 0.0151，与计分题 rank 1 最低值 0.1349 明显分离——是否引入“重排分阈值拒答”（避免检索硬凑、生成强行回答）留待阶段七评估。

---

## 关键参数

| 参数 | 当前值 | 位置 | 说明 |
|---|---|---|---|
| CHUNK_SIZE | 800 | `src/splitter.py` | 目标块大小（字符）。T1 对比过 400（更差，见调优实验 T1），维持基线；v2.0 阶段一已按 800/150 重建索引（库内 111 条） |
| CHUNK_OVERLAP | 150 | `src/splitter.py` | 相邻块重叠字符数。太小跨边界信息丢失，太大重复与存储成本增加 |
| EMBEDDING_MODEL | BAAI/bge-m3 | `.env`（默认值在 `src/config.py`） | Embedding 模型（硅基流动），输出 1024 维 |
| EMBED_BATCH_SIZE | 32 | `src/config.py` | 单次 Embedding 请求的最大文本条数 |
| COLLECTION_NAME | rag_mvp_docs | `src/config.py` | Chroma 集合名（3~512 字符、首尾字母数字） |
| top_k | 5 | `src/retriever.py` | 检索返回条数（DEFAULT_TOP_K），可传参覆盖 |
| BM25_K1 | 1.5 | `src/bm25_store.py` | BM25 词频饱和参数；属打分参数不写入索引，调参无需重建 |
| BM25_B | 0.75 | `src/bm25_store.py` | BM25 长度归一化强度（0 不归一化 / 1 完全归一化） |
| VECTOR_CANDIDATES | 20 | `src/hybrid_retriever.py` | 混合检索：向量路候选数（融合输入池，规划起点值） |
| BM25_CANDIDATES | 20 | `src/hybrid_retriever.py` | 混合检索：BM25 路候选数（规划起点值） |
| RRF_K | 60 | `src/fusion.py` | RRF 平滑常数：压平头部名次优势，倾向两路共识 |
| RERANK_CANDIDATES | 20 | `src/hybrid_reranker.py` | 送进重排的融合候选数（规划起点值，`hybrid_rerank_search` 参数可覆盖） |
| RERANK_TOP_K | 5 | `src/hybrid_reranker.py` | 重排后最终条数（产品口径：进 Prompt 的上下文条数） |
| RERANK_MODEL | BAAI/bge-reranker-v2-m3 | `.env`（默认值在 `src/config.py`） | 重排模型（硅基流动 Rerank API） |
| LLM_MODEL | Qwen/Qwen3-8B | `.env`（默认值在 `src/config.py`） | 生成模型（硅基流动），调用时关闭思考模式 |
| LLM_TEMPERATURE | 0.2 | `src/generator.py` | 生成随机性；低温保证答案稳定、评估可复现 |

---

## 决策记录与踩坑

1. **环境选 conda 而非 .venv**：用户主动要求用 conda 专用环境 `rag-one` 做隔离，`.venv` 已删除；全项目统一单一环境。
2. **`requirements.txt` 必须保持纯 ASCII 英文注释**：文件含 UTF-8 中文注释时，pip 在本机以 GBK 读取会抛 `UnicodeDecodeError`，改为英文注释后解决。
3. **运行一律加 `-X utf8`**：曾出现"脚本正常退出但无任何输出"，排查后确认是中文 Windows 的 GBK 编码链问题（非代码问题）；同时发现 `conda run` 会因 GBK 崩溃，故弃用。
4. **模型服务选硅基流动**：一个 API Key 同时覆盖 LLM 与 Embedding（BAAI/bge-m3），接口兼容 OpenAI 协议（Embedding 已于阶段四接入）。
5. **评估集用 JSONL 而非规划中的 json 数组**：一行一题，便于后续追加与流式读取；来源字段用 `expected_sources` 数组支持多来源题。
6. **第一版明确不做**：LangChain / LangGraph、Agent、多轮对话、扫描版 PDF OCR、Reranker、混合检索等（详见规划文档第 3.2 节）。
7. **Chroma 集合名有硬性约束**：3~512 字符、只含字母/数字/`._-`，且首尾必须是字母或数字——过短的名字（如 `t`）直接报错，故集合名定为 `rag_mvp_docs`。
8. **向量一律外部传入，关闭 Chroma 内置向量函数**：建集合时 `embedding_function=None`（默认会挂一个本地 ONNX 小模型）；忘传 embedding 时 Chroma 会显式报错，而不是静默算错。
9. **建集合参数只在“真正新建”时生效**：改距离度量等建表参数必须“先删后建”（`reset_collection`），对已存在的集合改代码无效。
10. **本机裸 `python` 不是项目环境**：默认解析到系统 Python 3.13（无项目依赖），运行一律用 `rag-one` 环境（激活或全路径）。
11. **服务端向量有微小跨请求抖动**：同一文本两次请求可能有 ≤0.002 的浮点差异（多数为 0），而不同文本差异约 0.1 / 余弦 ≈ 0.58——比较向量时阈值取 0.01 量级，勿用 1e-4。该抖动的检索侧可见效果：Top-8~10 近乎并列（分数差 < 0.001）的块顺序可能翻转（v2.0 阶段二复跑实测 q01/q05/q15），Top-7 以内与全部指标不受影响——重复评估的“稳定”以指标级为口径。**v2.0 阶段四补充（跨时段对照口径）**：跨时段（跨服务状态）对照的漂移带比同会话内宽——探针实测（q30 / q21 / q05）：同会话内同深度重跑逐位稳定、深度 20 vs 10 基本无差异（偶发边界位互换）；而早期基线产物与现时运行在弱相关团簇（各文档模板段、约第 4~20 名带）名次会整体漂移（最极端 9 → 4 位），且产物生成时刻的状态可现场复现——差异属服务状态时间差而非缺陷。对照口径：跨时段对照向量侧用软口径（以相关块名次与汇总指标为准）；BM25 等确定性链路不受此影响，可全程严格对照。
12. **切分粒度不是越细越好（有对比数据，详见调优实验 T1）**：同一知识库把 CHUNK_SIZE 从 800 降到 400（重叠同 150），chunk 数 10 → 32，25 题的来源级 Recall@5 反而从 100% 降到 93.5%，且 q01 首位命中从《差旅制度》变成《FAQ》。当前手册均为 800 字符内短文，"每篇整切"最优，维持 800/150。
13. **Qwen3-8B 默认开启思考模式（生成时必须关闭）**：不传 `extra_body={"enable_thinking": False}` 时，一次最小问答耗时约 14.7s、completion 399 token（其中思考链 397）；关闭后 0.5s、1 token。RAG 照资料答题用不到思考链，`generator.py` 已默认关闭（返回结构详见附录知识笔记）。
14. **界面启动走 `python -m streamlit`**：streamlit 装好后可执行文件在环境的 `Scripts\` 目录（不在 PATH），直接敲 `streamlit run` 会提示无法识别命令；统一用 `python -X utf8 -m streamlit run app.py` 启动界面。
15. **语料扩写段是刻意保留的干扰项（v2.0）**：9 篇 Markdown 各自追加的模板化“扩展使用说明”段（规则说明 / 执行要点 / 常见误区等）跨文档高度相似，是混合检索实验的 hard negative 与“多副本”观察点，不是数据事故；chunk 级标注对这类段落从严判定（仅含支撑答案的具体陈述才标）。
16. **BM25 手写实现而非引库（v2.0 阶段三）**：规划允许 `rank-bm25` 或手写，选择手写——公式透明、打分免引库（仅分词新增 jieba 0.42.1）、分词与并列兜底可控（同分按 chunk id 升序）。IDF 取 Lucene 变体 `ln(1+(N-df+0.5)/(df+0.5))`，恒为正、无负分（避免高 df 词把总分压低）；索引只持久化“可重建数据”（原文 + 分词 + 倒排 + avgdl），k1/b 属打分参数不写入索引——后续调参实验无需重建。
17. **语料冻结是字节级纪律（v2.0 阶段三验收实测）**：`03-attendance.md` 在基线生成之后被改动 1 行（`---` 分隔线被删，18489 → 18486 字节），造成 Chroma 索引（旧文本）与当前语料 / BM25 索引（新文本）在 2 个块上不一致、`corpus-version.md` 指纹过时——已恢复提交版并重建 BM25 闭环。两条配套教训：① 用 git 恢复文件不能直接 `git checkout`（本机 autocrlf 会 LF→CRLF 改变字节），须用 `git show` 取 blob 原始字节写入，指纹才与 corpus-version.md 一致；② 验收必须做「索引 × 切分 × 语料指纹」三方对齐，任何一处漂移都会让指标对照失去公平性。
18. **融合层用 RRF、只用排名不用分数（v2.0 阶段四）**：余弦相似度与 BM25 分数不同量纲（余弦约 0~1 且分布集中，BM25 无上界、量级随语料变化），加权相加会让某一路的分数尺度吞噬另一路；RRF 只取名次 `Σ 1/(k+rank)`，免归一化、免训练、可人工复算。k=60（规划起点值）：k 越小越偏向“单路头部”，越大越压平差距、趋于共识；本库实测共识策略成立——相对向量路改善 6 题、零退化，相对 BM25 路改善 4 题 / 2 题首位各退 1 位（q03 / q16 仍居 Top-3，机制详见知识笔记 D4）。融合结果保留每条命中的两路原始排名与分数（`vector_rank / vector_score / bm25_rank / bm25_score`），未命中路显式 `None`；同分按 chunk id 升序兜底（与 BM25 一致）。
19. **Reranker 独立封装走 HTTP 直连、失败回退不断链（v2.0 阶段五）**：rerank 不在 OpenAI 端点集内，用 `httpx` 直连 `{base_url}/rerank`（httpx 本就是 openai SDK 的底层依赖，按“直接 import 就显式声明”写入 requirements）；接口 `rerank(question, candidates, top_k)` 与供应商解耦，换模型 / 供应商只改 `src/reranker.py`。设计四要点：① `top_n=len(texts)` 拿回全部候选分数、在本地排序截断（tie-break 与字段控制留在自己手里，同分保持输入顺序）；② 空候选短路不发请求（实测 API 对空列表报 400）；③ 失败抛 `RerankError` 不吞错，组合层 `fallback=True` 回退融合 Top-K 并打印 `[WARN]`、`fallback=False` 严格抛错——两种都满足“明确报错或回退，不返回半截结果”；④ 重排是“贵”操作（每题一次调用、20 候选约 8.1k tokens、P50 +约 760ms），只处理 20 条窄候选——链路定型为“宽召回 + 窄精排”。
20. **端到端评估的判定口径（v2.0 阶段六）**：答案按「核心结论与期望一致」判定（错误拒答判否；冗余不误导不扣分）；引用用严格口径——答案标注的每个引用编号对应块均须含支撑结论的直接依据（点名问题对象的规则句 / 数字），间接相关与无关块判否；拒答题（q22~q24）不纳入引用准确率分母（正确性由拒答准确率覆盖）。该口径下引用准确率 E1 62.1% / E4 79.3%，未达 90% 目标，主要误差源是生成端「多标编号」（把 Top-5 中无关模板块一并标入）；如实记录不回填，留待阶段七作为界面观察项。

---

## 下一步

- v1.0 七个阶段已全部完成（MVP 完成定义 10/10，见“工作记录 → v1.0 → 收尾”）。
- **v2.0 进行中**（规划见 `RAG-v2.0学习规划.md`）：
  - 阶段一“冻结语料与评估标注”、阶段二“建立 v1.0 可重复评估基线”、阶段三“实现 BM25 检索”、阶段四“实现混合检索与 RRF 融合”、阶段五“接入 Reranker”、阶段六“端到端对照实验”已完成并验收（见“工作记录 → v2.0”）；
  - 下一环节：阶段七“工程化与界面升级”——把验证有效的链路接入 Streamlit（检索模式选择、候选数与 Top-K 设置、引用展示、四阶段详情与耗时、索引版本与 chunk 数），并处理 v1.0 遗留工程项（索引“先建后切”重建、临时断言转 pytest、依赖版本固定、README 三态标注）；
  - 人工评估表 `data/eval/eval-report.md` 已按 E1 / E4 双链路完成 32 题判定（含指标汇总、检索层与端到端对照、失败案例；端到端结论：E4 答案正确率 100%、引用准确率 79.3%，均优于 E1）。

---

## 参考资料

- [RAG-MVP学习规划.md](./RAG-MVP学习规划.md)：总规划、技术栈、七阶段验收清单、评估指标（Recall@5 ≥ 80% 等）
- [RAG-v2.0学习规划.md](./RAG-v2.0学习规划.md)：v2.0 规划——语料冻结、BM25 / RRF / Reranker、四方案对照实验与成功标准
- [data/README.md](./data/README.md)：知识库数据集说明
