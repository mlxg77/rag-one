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
| 四 ~ 七 | RRF 融合 / Reranker / 对照实验 / 工程化 | 未开始 |

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
| chromadb | 1.5.9 | 向量数据库（本地持久化） |
| pymupdf | 1.28.2 | PDF 文本提取（导入名 `import pymupdf`） |
| streamlit | 1.64.0 | Web 界面（附带依赖 pandas / pyarrow 等自动安装） |
| pytest | 9.1.1 | 测试 |

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
│   │   └── eval-report.md    # 人工评估表（v2.0：32 题逐题走查记录）
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
│   └── bm25_store.py         # v2.0 阶段三：BM25 关键词检索（已完成）
├── ingest.py                 # 阶段四：索引入口（已完成）
├── ingest_bm25.py            # v2.0 阶段三：BM25 索引入口（已完成）
├── app.py                    # 阶段七：Streamlit 界面（已完成）
├── evaluation/               # v2.0：离线检索评估（正式包）
│   ├── __init__.py
│   ├── metrics.py            # 指标纯函数：HitRank / Recall@K / RR@K / 百分位
│   └── evaluate_retrieval.py # 评估 CLI：一条命令跑完全部题目 → JSON + Markdown
├── tests/
│   └── test_bm25.py          # v2.0 阶段三：BM25 单元测试（pytest，6 用例）
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

---

## 附录

> 与各版本（v1.0 / v2.0）开发阶段平行的独立记录线，内部分两条子线，性质不同、分开归档：
>
> - **调优实验**（编号 T1、T2……）：凡「改一个参数 → 重建索引 → 用固定评估集对比效果」的对比实验（T1 时为 25 题，v2.0 起为 32 题）。本板块保留“为什么是这个值”的完整证据链；「关键参数」表只反映当前生效值。
> - **知识笔记**（不占 T 编号、非实验）：开发中实测沉淀的 API / 协议结构知识。

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
11. **服务端向量有微小跨请求抖动**：同一文本两次请求可能有 ≤0.002 的浮点差异（多数为 0），而不同文本差异约 0.1 / 余弦 ≈ 0.58——比较向量时阈值取 0.01 量级，勿用 1e-4。该抖动的检索侧可见效果：Top-8~10 近乎并列（分数差 < 0.001）的块顺序可能翻转（v2.0 阶段二复跑实测 q01/q05/q15），Top-7 以内与全部指标不受影响——重复评估的“稳定”以指标级为口径。
12. **切分粒度不是越细越好（有对比数据，详见调优实验 T1）**：同一知识库把 CHUNK_SIZE 从 800 降到 400（重叠同 150），chunk 数 10 → 32，25 题的来源级 Recall@5 反而从 100% 降到 93.5%，且 q01 首位命中从《差旅制度》变成《FAQ》。当前手册均为 800 字符内短文，"每篇整切"最优，维持 800/150。
13. **Qwen3-8B 默认开启思考模式（生成时必须关闭）**：不传 `extra_body={"enable_thinking": False}` 时，一次最小问答耗时约 14.7s、completion 399 token（其中思考链 397）；关闭后 0.5s、1 token。RAG 照资料答题用不到思考链，`generator.py` 已默认关闭（返回结构详见附录知识笔记）。
14. **界面启动走 `python -m streamlit`**：streamlit 装好后可执行文件在环境的 `Scripts\` 目录（不在 PATH），直接敲 `streamlit run` 会提示无法识别命令；统一用 `python -X utf8 -m streamlit run app.py` 启动界面。
15. **语料扩写段是刻意保留的干扰项（v2.0）**：9 篇 Markdown 各自追加的模板化“扩展使用说明”段（规则说明 / 执行要点 / 常见误区等）跨文档高度相似，是混合检索实验的 hard negative 与“多副本”观察点，不是数据事故；chunk 级标注对这类段落从严判定（仅含支撑答案的具体陈述才标）。
16. **BM25 手写实现而非引库（v2.0 阶段三）**：规划允许 `rank-bm25` 或手写，选择手写——公式透明、零新增依赖、分词与并列兜底可控（同分按 chunk id 升序）。IDF 取 Lucene 变体 `ln(1+(N-df+0.5)/(df+0.5))`，恒为正、无负分（避免高 df 词把总分压低）；索引只持久化“可重建数据”（原文 + 分词 + 倒排 + avgdl），k1/b 属打分参数不写入索引——后续调参实验无需重建。
17. **语料冻结是字节级纪律（v2.0 阶段三验收实测）**：`03-attendance.md` 在基线生成之后被改动 1 行（`---` 分隔线被删，18489 → 18486 字节），造成 Chroma 索引（旧文本）与当前语料 / BM25 索引（新文本）在 2 个块上不一致、`corpus-version.md` 指纹过时——已恢复提交版并重建 BM25 闭环。两条配套教训：① 用 git 恢复文件不能直接 `git checkout`（本机 autocrlf 会 LF→CRLF 改变字节），须用 `git show` 取 blob 原始字节写入，指纹才与 corpus-version.md 一致；② 验收必须做「索引 × 切分 × 语料指纹」三方对齐，任何一处漂移都会让指标对照失去公平性。

---

## 下一步

- v1.0 七个阶段已全部完成（MVP 完成定义 10/10，见“工作记录 → v1.0 → 收尾”）。
- **v2.0 进行中**（规划见 `RAG-v2.0学习规划.md`）：
  - 阶段一“冻结语料与评估标注”、阶段二“建立 v1.0 可重复评估基线”、阶段三“实现 BM25 检索”已完成并验收（见“工作记录 → v2.0”）；
  - 下一环节：阶段四“实现 RRF 融合”——把向量与 BM25 两路排名做倒数排名融合，在同一评估集上与两条单路对照；
  - 人工评估表 `data/eval/eval-report.md` 已同步为 32 题 v2.0 版（目标以 v2.0 规划第 5 节阶段六为准），待阶段六端到端时逐题填写。

---

## 参考资料

- [RAG-MVP学习规划.md](./RAG-MVP学习规划.md)：总规划、技术栈、七阶段验收清单、评估指标（Recall@5 ≥ 80% 等）
- [RAG-v2.0学习规划.md](./RAG-v2.0学习规划.md)：v2.0 规划——语料冻结、BM25 / RRF / Reranker、四方案对照实验与成功标准
- [data/README.md](./data/README.md)：知识库数据集说明
