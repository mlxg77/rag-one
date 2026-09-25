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
| 四 | 建立向量索引 | `config.py` / `embeddings.py` / `vector_store.py` / `indexer.py` / `ingest.py` | 未开始 |
| 五 | 实现并验证检索 | `retriever.py` | 未开始 |
| 六 | 实现答案生成 | `generator.py` / `rag.py` / `chat.py` | 未开始 |
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

1. **所有脚本必须加 `-X utf8` 运行**。本机中文 Windows 默认 GBK 编码，不加会导致中文输出乱码甚至丢输出：

   ```powershell
   python -X utf8 src/loaders.py
   ```

2. **`src` 包内模块用 `-m` 从项目根运行**（包内导入写 `src.xxx` 全路径）：

   ```powershell
   python -X utf8 -m src.splitter
   ```

3. **不要使用 `conda run`**。conda 24.5.0 在本机中文环境下捕获中文输出会崩溃（UnicodeEncodeError）或吞掉输出；直接激活环境或用环境内 python 全路径运行。

---

## 项目结构

```text
rag-one/
├── data/
│   ├── raw/                  # 10 篇制度手册（知识库）
│   ├── eval/questions.jsonl  # 25 题评估集（JSONL，一行一题）
│   └── README.md             # 数据集说明
├── src/
│   ├── __init__.py
│   ├── loaders.py            # 阶段二：文档加载（已完成）
│   └── splitter.py           # 阶段三：文本切分（已完成）
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

---

## 关键参数

| 参数 | 当前值 | 位置 | 说明 |
|---|---|---|---|
| CHUNK_SIZE | 800 | `src/splitter.py` | 目标块大小（字符）。太小上下文不完整，太大检索不精确 |
| CHUNK_OVERLAP | 150 | `src/splitter.py` | 相邻块重叠字符数。太小跨边界信息丢失，太大重复与存储成本增加 |
| top_k | 5（计划） | `src/retriever.py` | 检索返回条数，阶段五使用 |

---

## 决策记录与踩坑

1. **环境选 conda 而非 .venv**：用户主动要求用 conda 专用环境 `rag-one` 做隔离，`.venv` 已删除；全项目统一单一环境。
2. **`requirements.txt` 必须保持纯 ASCII 英文注释**：文件含 UTF-8 中文注释时，pip 在本机以 GBK 读取会抛 `UnicodeDecodeError`，改为英文注释后解决。
3. **运行一律加 `-X utf8`**：曾出现"脚本正常退出但无任何输出"，排查后确认是中文 Windows 的 GBK 编码链问题（非代码问题）；同时发现 `conda run` 会因 GBK 崩溃，故弃用。
4. **模型服务选硅基流动**（阶段四接入）：一个 API Key 同时覆盖 LLM 与 Embedding（BAAI/bge-m3），接口兼容 OpenAI 协议。
5. **评估集用 JSONL 而非规划中的 json 数组**：一行一题，便于后续追加与流式读取；来源字段用 `expected_sources` 数组支持多来源题。
6. **第一版明确不做**：LangChain / LangGraph、Agent、多轮对话、扫描版 PDF OCR、Reranker、混合检索等（详见规划文档第 3.2 节）。

---

## 下一步

- 阶段四（待启动）：配置 `.env`（`OPENAI_API_KEY` / `OPENAI_BASE_URL`），实现 `config.py` → `embeddings.py` → `vector_store.py` → `indexer.py` → `ingest.py`，跑通"一条命令建立索引"。

---

## 参考资料

- [RAG-MVP学习规划.md](./RAG-MVP学习规划.md)：总规划、技术栈、七阶段验收清单、评估指标（Recall@5 ≥ 80% 等）
- [data/README.md](./data/README.md)：知识库数据集说明
