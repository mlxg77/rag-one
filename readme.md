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

| 阶段 | 内容 | 产出 | 状态 |
|---|---|---|---|
| 一 | 准备知识库和测试问题 | `data/raw/` 10 篇手册 + `data/eval/questions.jsonl` 25 题 | 已完成并验收 |
| 二 | 实现文档加载 | `src/loaders.py` | 已完成并验收 |
| 三 | 实现文本切分 | `src/splitter.py` | 已完成并验收 |
| 四 | 建立向量索引 | `src/config.py` / `src/embeddings.py` / `src/vector_store.py` / `src/indexer.py` / `ingest.py` | 已完成并验收 |
| 五 | 实现并验证检索 | `src/retriever.py` | 已完成并验收 |
| 六 | 实现答案生成 | `src/generator.py` / `src/rag.py` | 已完成并验收 |
| 七 | 增加简单界面 | `app.py`（Streamlit） | 未开始 |

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

---

## 项目结构

```text
rag-one/
├── data/
│   ├── raw/                  # 10 篇制度手册（知识库）
│   ├── eval/questions.jsonl  # 25 题评估集（JSONL，一行一题）
│   └── README.md             # 数据集说明
├── storage/
│   └── chroma/               # ChromaDB 持久化索引（git 忽略，可用 ingest.py 重建）
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
│   └── rag.py                # 阶段六：检索→生成主流程（已完成）
├── ingest.py                 # 阶段四：索引入口（已完成）
├── .env.example              # 环境变量模板（.env 含密钥，被 git 忽略）
├── RAG-MVP学习规划.md         # 总规划：目标、技术栈、七阶段验收清单
├── readme.md                 # 本文件
├── requirements.txt          # 纯 ASCII 英文注释（见"踩坑记录"）
└── .gitignore                # 忽略 .venv/ __pycache__/ .env storage/chroma/
```

---

## 工作记录

### 阶段一：知识库与评估集（已完成并验收）

**知识库** `data/raw/`：虚构的"星云科技公司制度手册"共 10 篇 Markdown（版本 2026.1，生效日期 2026-01-01）：

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

### 阶段二：文档加载 `src/loaders.py`（已完成并验收）

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

### 阶段三：文本切分 `src/splitter.py`（已完成并验收）

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

### 阶段四：建立向量索引（已完成并验收）

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

### 阶段五：Top-K 检索 `src/retriever.py`（已完成并验收）

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

### 阶段六：答案生成 `src/generator.py` + `src/rag.py`（已完成并验收）

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

---

## 附录：

> 与七个开发阶段平行的独立记录线：凡「改一个参数 → 重建索引 → 用 25 题评估集对比效果」的实验都记在这里，编号 T1、T2……「关键参数」表只反映当前生效值，本板块保留“为什么是这个值”的完整证据链。另设「知识笔记」小节，收纳开发中实测沉淀的 API / 协议结构知识（不占 T 编号、非实验）。

### T1 · CHUNK_SIZE：800 → 400（重叠 150 不变）

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

### 知识笔记 · ChatCompletion 返回结构（阶段六 generator 实测）

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
| CHUNK_SIZE | 800 | `src/splitter.py` | 目标块大小（字符）。T1 已对比 400 更优（见调优实验 T1），第二轮实验后已恢复基线并重建索引 |
| CHUNK_OVERLAP | 150 | `src/splitter.py` | 相邻块重叠字符数。太小跨边界信息丢失，太大重复与存储成本增加 |
| EMBEDDING_MODEL | BAAI/bge-m3 | `.env`（默认值在 `src/config.py`） | Embedding 模型（硅基流动），输出 1024 维 |
| EMBED_BATCH_SIZE | 32 | `src/config.py` | 单次 Embedding 请求的最大文本条数 |
| COLLECTION_NAME | rag_mvp_docs | `src/config.py` | Chroma 集合名（3~512 字符、首尾字母数字） |
| top_k | 5 | `src/retriever.py` | 检索返回条数（DEFAULT_TOP_K），可传参覆盖 |
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
11. **服务端向量有微小跨请求抖动**：同一文本两次请求可能有 ≤0.002 的浮点差异（多数为 0），而不同文本差异约 0.1 / 余弦 ≈ 0.58——比较向量时阈值取 0.01 量级，勿用 1e-4。
12. **切分粒度不是越细越好（有对比数据，详见调优实验 T1）**：同一知识库把 CHUNK_SIZE 从 800 降到 400（重叠同 150），chunk 数 10 → 32，25 题的来源级 Recall@5 反而从 100% 降到 93.5%，且 q01 首位命中从《差旅制度》变成《FAQ》。当前手册均为 800 字符内短文，"每篇整切"最优，维持 800/150。
13. **Qwen3-8B 默认开启思考模式（生成时必须关闭）**：不传 `extra_body={"enable_thinking": False}` 时，一次最小问答耗时约 14.7s、completion 399 token（其中思考链 397）；关闭后 0.5s、1 token。RAG 照资料答题用不到思考链，`generator.py` 已默认关闭（返回结构详见附录知识笔记）。

---

## 下一步

- 阶段七（待启动）：Streamlit 界面 `app.py`——文档上传 / 重建索引按钮 / 问题输入 / 答案与引用展示 / 检索片段折叠区；界面只调用 RAG 模块，不把核心逻辑写进页面。

---

## 参考资料

- [RAG-MVP学习规划.md](./RAG-MVP学习规划.md)：总规划、技术栈、七阶段验收清单、评估指标（Recall@5 ≥ 80% 等）
- [data/README.md](./data/README.md)：知识库数据集说明
