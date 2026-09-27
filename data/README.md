# 星云科技员工手册：RAG 入门数据集

这是一套完全虚构的中文员工手册，用于学习和测试检索增强生成（RAG）。公司、人员、制度和金额均为模拟信息，不能作为真实劳动或财务制度依据。

## 数据集内容

- `raw/`：10 份知识库文件——9 份 Markdown 专项制度（`01`～`09`）与 1 份 PDF 版常见问题（`10-faq.pdf`，6 页）
- `eval/questions.jsonl`：32 条评估问题（25 条原题 + 7 条新增），字段为 `id / question / expected_answer / expected_sources / relevant_chunk_ids / type`
- `eval/eval-report.md`：32 题人工评估表，用于逐题走查检索与生成质量并汇总指标
- `eval/corpus-version.md`：v2.0 语料版本快照（文件指纹 / 切分参数 / chunk 统计）
- `eval/baseline-v1.json` + `eval/baseline-v1.md`：v1.0 向量检索基线结果（32 题；机器可读 JSON + 可读报告，配套评估脚本见仓库 `evaluation/`）
- `eval/run-bm25.json` + `eval/run-bm25.md`：BM25 关键词检索评估结果（32 题，与向量基线同口径，可直接对照）
- `eval/run-hybrid.json` + `eval/run-hybrid.md`：混合检索（向量 + BM25 → RRF 融合）评估结果（32 题，与基线 / BM25 同口径，含每条命中的两路名次）
- `eval/run-hybrid-rerank.json` + `eval/run-hybrid-rerank.md`：混合检索 + Reranker 精排评估结果（32 题，与前述同口径，含每条命中的重排前融合名次与重排分数）

## 推荐用法

1. 资料位于 `data/raw/`，直接加载使用；Markdown 按纯文本读取，`10-faq.pdf` 需 PDF 文本解析（每页一条记录）。
2. 首轮参数建议 `chunk_size=800`、`chunk_overlap=150`、`top_k=5`（与 rag-one 当前配置一致）。
3. 建立索引后，用 `eval/questions.jsonl` 逐条做检索评估，再按 `eval/eval-report.md` 走查端到端答案。
4. 调试时同时输出召回片段、相似度、来源文件和最终答案。

## 建议的元数据

```json
{
  "source": "04-leave-policy.md",
  "title": "休假与请假制度",
  "section": "病假",
  "version": "2026.1",
  "effective_date": "2026-01-01"
}
```

## 数据集设计

文档故意包含一些容易混淆的规则：

- 普通报销期限是 30 个自然日，差旅报销期限是返程后 15 个自然日。
- 国内酒店标准按城市类别和职级变化。
- 正式员工与试用期员工的远程办公规则不同。
- 病假、事假和年假的申请时限、证明材料不同。
- IT 服务台与安全事件的报告渠道不同。

2026.1 版语料在正式条款后追加了约 130 行扩展说明（办理口径、角色责任、常见场景），且各文件的通用段落表述高度相似；常见问题改以 `10-faq.pdf` 形式提供。这些差异与安排可以用于观察文本切分、召回和引用是否准确，也便于观察相似段落干扰与 PDF 解析的影响。

## 使用限制

本数据集可自由用于个人学习、演示和测试。不要将其中制度用于现实组织。
