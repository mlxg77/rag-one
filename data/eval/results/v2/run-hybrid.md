# 检索评估报告：run-hybrid

## 运行信息

| 项 | 值 |
|---|---|
| 时间 | 2026-09-27T17:32:39 |
| 模式 | hybrid |
| top_k | 10 |
| 集合 / 向量数 | rag_mvp_docs / 111 |
| Embedding | BAAI/bge-m3 |
| 题目数 / 参与统计 | 32 / 31（拒答题不计入） |

## 汇总指标

| 指标 | 值 | 说明 |
|---|---:|---|
| Recall@5 | 100.0% | 前 5 命中中含任一相关块的题占比 |
| Recall@10 | 100.0% | 前 10 命中中含任一相关块的题占比 |
| MRR@10 | 0.925 | 首个相关块排名的倒数均值 |
| 相关块覆盖（Top-10） | 91.7% | 命中相关块数 / 标注总数 |
| 延迟 P50 / P95 | 195 / 458 ms | 单题端到端（含查询向量化网络时间） |

## 分题型统计

| 题型 | 题数 | Recall@5 | MRR@10 |
|---|---:|---:|---:|
| confusable | 4 | 100.0% | 0.708 |
| direct | 9 | 100.0% | 1.000 |
| keyword | 5 | 100.0% | 1.000 |
| multi_source | 5 | 100.0% | 0.867 |
| reasoning | 2 | 100.0% | 1.000 |
| semantic | 1 | 100.0% | 0.500 |
| table | 1 | 100.0% | 1.000 |
| trap | 2 | 100.0% | 1.000 |
| unanswerable | 2 | 100.0% | 1.000 |

## Recall@5 未命中的题

无。

## 逐题明细

| 题 | 题型 | HitRank | RR@10 | R@5 | R@10 | 延迟ms | Top-1 |
|---|---|---:|---:|---:|---:|---:|---|
| q01 | direct | 1 | 1.000 | 1 | 1 | 2735 | 10-faq.pdf:page-1:chunk-0 |
| q02 | table | 1 | 1.000 | 1 | 1 | 192 | 10-faq.pdf:page-3:chunk-1 |
| q03 | confusable | 2 | 0.500 | 1 | 1 | 202 | 05-expense-policy.md:chunk-0 |
| q04 | reasoning | 1 | 1.000 | 1 | 1 | 186 | 05-expense-policy.md:chunk-0 |
| q05 | direct | 1 | 1.000 | 1 | 1 | 192 | 05-expense-policy.md:chunk-5 |
| q06 | direct | 1 | 1.000 | 1 | 1 | 458 | 05-expense-policy.md:chunk-6 |
| q07 | confusable | 1 | 1.000 | 1 | 1 | 188 | 04-leave-policy.md:chunk-0 |
| q08 | direct | 1 | 1.000 | 1 | 1 | 178 | 04-leave-policy.md:chunk-0 |
| q09 | reasoning | 1 | 1.000 | 1 | 1 | 217 | 04-leave-policy.md:chunk-0 |
| q10 | direct | 1 | 1.000 | 1 | 1 | 181 | 07-remote-work.md:chunk-0 |
| q11 | multi_source | 1 | 1.000 | 1 | 1 | 276 | 07-remote-work.md:chunk-0 |
| q12 | multi_source | 1 | 1.000 | 1 | 1 | 208 | 10-faq.pdf:page-1:chunk-0 |
| q13 | direct | 1 | 1.000 | 1 | 1 | 186 | 07-remote-work.md:chunk-0 |
| q14 | direct | 1 | 1.000 | 1 | 1 | 191 | 02-onboarding.md:chunk-0 |
| q15 | direct | 1 | 1.000 | 1 | 1 | 225 | 02-onboarding.md:chunk-6 |
| q16 | multi_source | 3 | 0.333 | 1 | 1 | 214 | 08-information-security.md:chunk-1 |
| q17 | multi_source | 1 | 1.000 | 1 | 1 | 228 | 10-faq.pdf:page-4:chunk-0 |
| q18 | trap | 1 | 1.000 | 1 | 1 | 452 | 09-it-support.md:chunk-0 |
| q19 | trap | 1 | 1.000 | 1 | 1 | 178 | 09-it-support.md:chunk-6 |
| q20 | confusable | 3 | 0.333 | 1 | 1 | 261 | 10-faq.pdf:page-1:chunk-0 |
| q21 | direct | 1 | 1.000 | 1 | 1 | 195 | 03-attendance.md:chunk-4 |
| q22 | unanswerable | 1 | 1.000 | 1 | 1 | 230 | 10-faq.pdf:page-1:chunk-0 |
| q23 | unanswerable | 1 | 1.000 | 1 | 1 | 214 | 04-leave-policy.md:chunk-0 |
| q24 | unanswerable | — | — | — | — | 258 | 10-faq.pdf:page-1:chunk-0 |
| q25 | multi_source | 1 | 1.000 | 1 | 1 | 191 | 01-company-overview.md:chunk-6 |
| q26 | keyword | 1 | 1.000 | 1 | 1 | 203 | 09-it-support.md:chunk-2 |
| q27 | keyword | 1 | 1.000 | 1 | 1 | 180 | 08-information-security.md:chunk-0 |
| q28 | keyword | 1 | 1.000 | 1 | 1 | 188 | 09-it-support.md:chunk-0 |
| q29 | keyword | 1 | 1.000 | 1 | 1 | 202 | 09-it-support.md:chunk-3 |
| q30 | keyword | 1 | 1.000 | 1 | 1 | 183 | 08-information-security.md:chunk-0 |
| q31 | confusable | 1 | 1.000 | 1 | 1 | 192 | 01-company-overview.md:chunk-0 |
| q32 | semantic | 2 | 0.500 | 1 | 1 | 162 | 10-faq.pdf:page-1:chunk-0 |

