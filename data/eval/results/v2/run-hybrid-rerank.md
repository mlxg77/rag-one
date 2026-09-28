# 检索评估报告：run-hybrid-rerank

## 文件说明

- v2.0 检索层评估 hybrid + 重排实验；同名 `.json` 为权威原始数据，本报告为其渲染（本说明为归档补注）。
- 实验内容：bge-reranker-v2-m3 对融合候选逐对精排取 Top-K。
- 实验角色：四组对照最后一组——baseline-vector → run-bm25 → run-hybrid → **run-hybrid-rerank（本组）**。
- 生成与状态：2026-09-27 由 `evaluation/evaluate_retrieval.py` 生成；属 v2.0 冻结快照。
- 读者：人读 md，程序读 JSON。

## 运行信息

| 项 | 值 |
|---|---|
| 时间 | 2026-09-27T17:53:26 |
| 模式 | hybrid_rerank |
| top_k | 10 |
| 集合 / 向量数 | rag_mvp_docs / 111 |
| Embedding | BAAI/bge-m3 |
| 题目数 / 参与统计 | 32 / 31（拒答题不计入） |

## 汇总指标

| 指标 | 值 | 说明 |
|---|---:|---|
| Recall@5 | 100.0% | 前 5 命中中含任一相关块的题占比 |
| Recall@10 | 100.0% | 前 10 命中中含任一相关块的题占比 |
| MRR@10 | 1.000 | 首个相关块排名的倒数均值 |
| 相关块覆盖（Top-10） | 94.8% | 命中相关块数 / 标注总数 |
| 延迟 P50 / P95 | 954 / 2057 ms | 单题端到端（含查询向量化网络时间） |

## 分题型统计

| 题型 | 题数 | Recall@5 | MRR@10 |
|---|---:|---:|---:|
| confusable | 4 | 100.0% | 1.000 |
| direct | 9 | 100.0% | 1.000 |
| keyword | 5 | 100.0% | 1.000 |
| multi_source | 5 | 100.0% | 1.000 |
| reasoning | 2 | 100.0% | 1.000 |
| semantic | 1 | 100.0% | 1.000 |
| table | 1 | 100.0% | 1.000 |
| trap | 2 | 100.0% | 1.000 |
| unanswerable | 2 | 100.0% | 1.000 |

## Recall@5 未命中的题

无。

## 逐题明细

| 题 | 题型 | HitRank | RR@10 | R@5 | R@10 | 延迟ms | Top-1 |
|---|---|---:|---:|---:|---:|---:|---|
| q01 | direct | 1 | 1.000 | 1 | 1 | 2222 | 10-faq.pdf:page-3:chunk-0 |
| q02 | table | 1 | 1.000 | 1 | 1 | 1646 | 10-faq.pdf:page-3:chunk-1 |
| q03 | confusable | 1 | 1.000 | 1 | 1 | 843 | 06-travel-policy.md:chunk-7 |
| q04 | reasoning | 1 | 1.000 | 1 | 1 | 870 | 05-expense-policy.md:chunk-0 |
| q05 | direct | 1 | 1.000 | 1 | 1 | 1014 | 05-expense-policy.md:chunk-5 |
| q06 | direct | 1 | 1.000 | 1 | 1 | 840 | 05-expense-policy.md:chunk-6 |
| q07 | confusable | 1 | 1.000 | 1 | 1 | 2057 | 04-leave-policy.md:chunk-4 |
| q08 | direct | 1 | 1.000 | 1 | 1 | 1512 | 04-leave-policy.md:chunk-0 |
| q09 | reasoning | 1 | 1.000 | 1 | 1 | 992 | 04-leave-policy.md:chunk-7 |
| q10 | direct | 1 | 1.000 | 1 | 1 | 926 | 10-faq.pdf:page-2:chunk-0 |
| q11 | multi_source | 1 | 1.000 | 1 | 1 | 1087 | 10-faq.pdf:page-2:chunk-0 |
| q12 | multi_source | 1 | 1.000 | 1 | 1 | 920 | 07-remote-work.md:chunk-2 |
| q13 | direct | 1 | 1.000 | 1 | 1 | 1033 | 07-remote-work.md:chunk-1 |
| q14 | direct | 1 | 1.000 | 1 | 1 | 953 | 02-onboarding.md:chunk-4 |
| q15 | direct | 1 | 1.000 | 1 | 1 | 897 | 02-onboarding.md:chunk-6 |
| q16 | multi_source | 1 | 1.000 | 1 | 1 | 1031 | 07-remote-work.md:chunk-7 |
| q17 | multi_source | 1 | 1.000 | 1 | 1 | 954 | 08-information-security.md:chunk-0 |
| q18 | trap | 1 | 1.000 | 1 | 1 | 1114 | 10-faq.pdf:page-4:chunk-1 |
| q19 | trap | 1 | 1.000 | 1 | 1 | 878 | 09-it-support.md:chunk-6 |
| q20 | confusable | 1 | 1.000 | 1 | 1 | 1009 | 03-attendance.md:chunk-1 |
| q21 | direct | 1 | 1.000 | 1 | 1 | 790 | 03-attendance.md:chunk-4 |
| q22 | unanswerable | 1 | 1.000 | 1 | 1 | 825 | 10-faq.pdf:page-1:chunk-0 |
| q23 | unanswerable | 1 | 1.000 | 1 | 1 | 1376 | 10-faq.pdf:page-5:chunk-0 |
| q24 | unanswerable | — | — | — | — | 1020 | 05-expense-policy.md:chunk-0 |
| q25 | multi_source | 1 | 1.000 | 1 | 1 | 1216 | 01-company-overview.md:chunk-0 |
| q26 | keyword | 1 | 1.000 | 1 | 1 | 817 | 09-it-support.md:chunk-0 |
| q27 | keyword | 1 | 1.000 | 1 | 1 | 985 | 08-information-security.md:chunk-7 |
| q28 | keyword | 1 | 1.000 | 1 | 1 | 932 | 09-it-support.md:chunk-0 |
| q29 | keyword | 1 | 1.000 | 1 | 1 | 847 | 09-it-support.md:chunk-0 |
| q30 | keyword | 1 | 1.000 | 1 | 1 | 874 | 08-information-security.md:chunk-0 |
| q31 | confusable | 1 | 1.000 | 1 | 1 | 971 | 01-company-overview.md:chunk-2 |
| q32 | semantic | 1 | 1.000 | 1 | 1 | 932 | 07-remote-work.md:chunk-4 |

