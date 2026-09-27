# 语料版本记录（v2.0 冻结）

- 生成日期：2026-09-27
- 语料目录：data/raw/
- 切分参数：CHUNK_SIZE=800，CHUNK_OVERLAP=150

统计：文档 10 篇（记录 15 条）→ chunk 111 个，平均 717.7 字符。

> 本文件是 rag-one v2.0 全部实验共用的语料版本快照；文件指纹为 SHA256 前 16 位。
> 冻结期内不得新增、重写或替换 data/raw 下的任何文件。
> 复查方式：重跑 `python -X utf8 -m tools.freeze_corpus`，比对指纹与统计。

## 文件清单与指纹

| 文件 | 字节数 | SHA256（前 16 位） |
|---|---:|---|
| 01-company-overview.md | 18822 | `5452f3831de7c49d` |
| 02-onboarding.md | 18696 | `9bee6f1ffb701571` |
| 03-attendance.md | 18489 | `28e8425c7dac3152` |
| 04-leave-policy.md | 18481 | `3640332f75e0b416` |
| 05-expense-policy.md | 18309 | `5d9c4127f059e760` |
| 06-travel-policy.md | 18443 | `df9ef7737fe21b67` |
| 07-remote-work.md | 18361 | `0aed7013ba8a7d3b` |
| 08-information-security.md | 18482 | `134f83c4051f26fe` |
| 09-it-support.md | 18167 | `014110f47ad4a9c2` |
| 10-faq.pdf | 573110 | `286ce0d8eeb4939b` |

## 每篇 chunk 分布

| 来源 | chunk 数 |
|---|---:|
| 01-company-overview.md | 12 |
| 02-onboarding.md | 11 |
| 03-attendance.md | 11 |
| 04-leave-policy.md | 11 |
| 05-expense-policy.md | 11 |
| 06-travel-policy.md | 11 |
| 07-remote-work.md | 11 |
| 08-information-security.md | 11 |
| 09-it-support.md | 11 |
| 10-faq.pdf | 11 |
