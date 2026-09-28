# v2.5 评估集冻结记录

- 首次冻结日期：2026-09-27
- C4 盲测追加冻结：2026-09-28

| 文件 | 题数 | SHA256 |
|---|---:|---|
| `data/eval/regression.jsonl` | 32 | `eda951adb529df41f89326bc3ff735e39306d70b1c8a98efd9a0d34018a12a63` |
| `data/eval/holdout.jsonl` | 15 | `6aa31eeb8c37c91600111386e63849bba83028cd4770b0a1eccd90ada4c2e1e2` |
| `data/eval/blind-v2.5.jsonl` | 20 | `92524f614d42b79b519c1ea606e27c573a7462b901c848d36b11919105717da1` |
| `data/eval/evidence-anchors.json` | 67 个题号 | `4a7e4b3ee8e7f858f4bd41df35e9e0ba46e9b5f425397aff6aeacfc731722938` |

holdout 类型分布：关键词 2、语义改写 3、相似章节干扰 2、多证据 4、拒答 4。

纪律：版本候选冻结前不得查看终验集的逐题运行结果；每套终验集最终运行一次后，不再据此修改系统并重复刷新分数。原 Holdout 与 C4 新盲测均已消费。
