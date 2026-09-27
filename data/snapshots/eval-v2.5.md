# v2.5 评估集冻结记录

冻结日期：2026-09-27

| 文件 | 题数 | SHA256 |
|---|---:|---|
| `data/eval/regression.jsonl` | 32 | `eda951adb529df41f89326bc3ff735e39306d70b1c8a98efd9a0d34018a12a63` |
| `data/eval/holdout.jsonl` | 15 | `6aa31eeb8c37c91600111386e63849bba83028cd4770b0a1eccd90ada4c2e1e2` |
| `data/eval/evidence-anchors.json` | 47 个题号 | `779de058ba81312e77fcf08eaadde30f5185f42b444e029ea06bb9720f372e49` |

holdout 类型分布：关键词 2、语义改写 3、相似章节干扰 2、多证据 4、拒答 4。

纪律：版本候选冻结前不得查看 holdout 的逐题运行结果；最终运行一次后，不再据此修改系统并重复刷新分数。
