# 数据目录

本目录是一套完全虚构的中文员工手册与评估数据，不代表真实组织制度。

## 内容

- `raw/`：9 份 Markdown 与 1 份 6 页 PDF，共 10 份冻结语料。
- `snapshots/corpus-v2.md`：v2/v2.5 使用的语料文件指纹与 800/150 切分统计。
- `eval/regression.jsonl`：32 题开发回归集，可反复运行。
- `eval/holdout.jsonl`：原 15 题独立保留集，已经消费。
- `eval/blind-v2.5.jsonl`：C4 冻结后的 20 题新盲测，已经消费。
- `eval/evidence-anchors.json`：与 chunk 参数无关的必要事实文本锚点。评估时映射到当前切分，避免 600/800/1000 参数下复用序号 ID 造成假结论。
- `eval/results/v2/`：v2.0 历史原始结果。
- `eval/results/v2.5/`：v2.5 原始结果；人工结论位于 `docs/experiments/` 与 `docs/reports/`。

## 冻结身份

截至 v2.5 学习项目 / 内部演示完成版：

| 文件 | SHA256 |
|---|---|
| `regression.jsonl` | `eda951adb529df41f89326bc3ff735e39306d70b1c8a98efd9a0d34018a12a63` |
| `holdout.jsonl` | `6aa31eeb8c37c91600111386e63849bba83028cd4770b0a1eccd90ada4c2e1e2` |
| `blind-v2.5.jsonl` | `92524f614d42b79b519c1ea606e27c573a7462b901c848d36b11919105717da1` |
| `evidence-anchors.json` | `4a7e4b3ee8e7f858f4bd41df35e9e0ba46e9b5f425397aff6aeacfc731722938` |

如后续修正标注，必须记录理由并重新运行所有对照，不可静默覆盖结果。

## 校验与使用

```powershell
python -m scripts.freeze_corpus
python -m evaluation.validate_dataset data/eval/regression.jsonl data/eval/holdout.jsonl data/eval/blind-v2.5.jsonl
python -m evaluation.evaluate_chunk_offline
```

chunk 和 Prompt 调优只能读取 Regression 或新增开发题。原 Holdout 与新盲测均不得用于选择参数或重复终验。
