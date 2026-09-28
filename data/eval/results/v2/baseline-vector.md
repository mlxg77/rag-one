# 检索评估报告：baseline-v1

## 文件说明

- v2.0 检索层评估基线段：v1.0 口径纯向量链（内部名 `baseline-v1`）；同名 `.json` 为权威原始数据，本报告为其渲染（本说明为归档补注）。
- 实验内容：bge-m3 向量 + Chroma 余弦，仅按相似度返回 Top-K。
- 实验角色：四组对照起点——**baseline-vector（本组）** → run-bm25 → run-hybrid → run-hybrid-rerank。
- 生成与状态：2026-09-27 由 `evaluation/evaluate_retrieval.py` 生成；属 v2.0 冻结快照。
- 读者：人读 md，程序读 JSON。

## 运行信息

| 项 | 值 |
|---|---|
| 时间 | 2026-09-27T16:01:27 |
| 模式 | vector |
| top_k | 10 |
| 集合 / 向量数 | rag_mvp_docs / 111 |
| Embedding | BAAI/bge-m3 |
| 题目数 / 参与统计 | 32 / 31（拒答题不计入） |

## 汇总指标

| 指标 | 值 | 说明 |
|---|---:|---|
| Recall@5 | 96.8% | 前 5 命中中含任一相关块的题占比 |
| Recall@10 | 100.0% | 前 10 命中中含任一相关块的题占比 |
| MRR@10 | 0.838 | 首个相关块排名的倒数均值 |
| 相关块覆盖（Top-10） | 84.8% | 命中相关块数 / 标注总数 |
| 延迟 P50 / P95 | 198 / 574 ms | 单题端到端（含查询向量化网络时间） |

## 分题型统计

| 题型 | 题数 | Recall@5 | MRR@10 |
|---|---:|---:|---:|
| confusable | 4 | 75.0% | 0.536 |
| direct | 9 | 100.0% | 0.778 |
| keyword | 5 | 100.0% | 1.000 |
| multi_source | 5 | 100.0% | 0.867 |
| reasoning | 2 | 100.0% | 1.000 |
| semantic | 1 | 100.0% | 0.500 |
| table | 1 | 100.0% | 1.000 |
| trap | 2 | 100.0% | 1.000 |
| unanswerable | 2 | 100.0% | 1.000 |

## Recall@5 未命中的题

- **q20** [confusable] 外出拜访客户会占用每周远程办公天数吗？
  - 相关块：03-attendance.md:chunk-1, 03-attendance.md:chunk-7
  - 实际 Top-5：10-faq.pdf:page-1:chunk-0, 07-remote-work.md:chunk-0, 10-faq.pdf:page-2:chunk-1, 07-remote-work.md:chunk-2, 10-faq.pdf:page-2:chunk-0

## 逐题明细

| 题 | 题型 | HitRank | RR@10 | R@5 | R@10 | 延迟ms | Top-1 |
|---|---|---:|---:|---:|---:|---:|---|
| q01 | direct | 2 | 0.500 | 1 | 1 | 737 | 06-travel-policy.md:chunk-5 |
| q02 | table | 1 | 1.000 | 1 | 1 | 159 | 10-faq.pdf:page-3:chunk-1 |
| q03 | confusable | 2 | 0.500 | 1 | 1 | 182 | 05-expense-policy.md:chunk-0 |
| q04 | reasoning | 1 | 1.000 | 1 | 1 | 242 | 05-expense-policy.md:chunk-0 |
| q05 | direct | 1 | 1.000 | 1 | 1 | 210 | 05-expense-policy.md:chunk-5 |
| q06 | direct | 2 | 0.500 | 1 | 1 | 234 | 05-expense-policy.md:chunk-5 |
| q07 | confusable | 1 | 1.000 | 1 | 1 | 574 | 04-leave-policy.md:chunk-4 |
| q08 | direct | 1 | 1.000 | 1 | 1 | 165 | 04-leave-policy.md:chunk-0 |
| q09 | reasoning | 1 | 1.000 | 1 | 1 | 206 | 04-leave-policy.md:chunk-0 |
| q10 | direct | 1 | 1.000 | 1 | 1 | 397 | 07-remote-work.md:chunk-0 |
| q11 | multi_source | 1 | 1.000 | 1 | 1 | 219 | 07-remote-work.md:chunk-0 |
| q12 | multi_source | 1 | 1.000 | 1 | 1 | 228 | 07-remote-work.md:chunk-0 |
| q13 | direct | 1 | 1.000 | 1 | 1 | 198 | 07-remote-work.md:chunk-1 |
| q14 | direct | 2 | 0.500 | 1 | 1 | 198 | 08-information-security.md:chunk-4 |
| q15 | direct | 1 | 1.000 | 1 | 1 | 240 | 02-onboarding.md:chunk-6 |
| q16 | multi_source | 3 | 0.333 | 1 | 1 | 150 | 08-information-security.md:chunk-1 |
| q17 | multi_source | 1 | 1.000 | 1 | 1 | 194 | 10-faq.pdf:page-4:chunk-0 |
| q18 | trap | 1 | 1.000 | 1 | 1 | 174 | 09-it-support.md:chunk-0 |
| q19 | trap | 1 | 1.000 | 1 | 1 | 229 | 09-it-support.md:chunk-6 |
| q20 | confusable | 7 | 0.143 | 0 | 1 | 233 | 10-faq.pdf:page-1:chunk-0 |
| q21 | direct | 2 | 0.500 | 1 | 1 | 211 | 03-attendance.md:chunk-3 |
| q22 | unanswerable | 1 | 1.000 | 1 | 1 | 161 | 10-faq.pdf:page-1:chunk-0 |
| q23 | unanswerable | 1 | 1.000 | 1 | 1 | 152 | 04-leave-policy.md:chunk-0 |
| q24 | unanswerable | — | — | — | — | 161 | 05-expense-policy.md:chunk-0 |
| q25 | multi_source | 1 | 1.000 | 1 | 1 | 221 | 01-company-overview.md:chunk-6 |
| q26 | keyword | 1 | 1.000 | 1 | 1 | 162 | 09-it-support.md:chunk-2 |
| q27 | keyword | 1 | 1.000 | 1 | 1 | 171 | 08-information-security.md:chunk-0 |
| q28 | keyword | 1 | 1.000 | 1 | 1 | 164 | 09-it-support.md:chunk-0 |
| q29 | keyword | 1 | 1.000 | 1 | 1 | 272 | 09-it-support.md:chunk-3 |
| q30 | keyword | 1 | 1.000 | 1 | 1 | 156 | 08-information-security.md:chunk-0 |
| q31 | confusable | 2 | 0.500 | 1 | 1 | 145 | 01-company-overview.md:chunk-3 |
| q32 | semantic | 2 | 0.500 | 1 | 1 | 237 | 10-faq.pdf:page-1:chunk-0 |

