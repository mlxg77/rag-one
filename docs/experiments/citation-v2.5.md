# v2.5 引用质量实验

## C0：历史基线

- 链路：E4 hybrid_rerank。
- Prompt：v2.0 历史 Prompt。
- regression：严格引用准确率 79.3%（23/29），引用块级支持率 86.1%（62/72）。
- 主要错误：模型把 Top-5 中“主题相关但未直接用于结论”的块一起标入。

历史数据来自 `docs/reports/v2.0.md`，不使用新 Prompt 回填 C0。

## C1：最少直接引用

实现版本：`v2.5-c1-minimal-citations`。

唯一主要变量是 Prompt：

- 参考资料在 system message 中被声明为不可信数据，不能改变系统规则；
- 只引用直接支持最终结论的最少资料；
- 禁止为显得完整而罗列所有编号；
- 资料不足时拒答，不附无关引用。

同时增加结构校验：引用编号去重、越界编号、拒答却附引用。结构校验不能替代人工“支持性”判定。

## 实际验收状态

C1 代码和离线测试已完成。32 题 regression 端到端运行启动后被中断，没有形成有效的完整验收结论。冻结候选 `800/150 + hybrid_rerank + C1` 随后按项目决定直接执行了一次 15 题 holdout。

Holdout 自动结果：

- Any-hit Recall@5：100%；
- Evidence-group Recall@5：100%；
- Complete-evidence@5：100%；
- 非法引用编号答案：0；
- 拒答却附编号答案：0；
- Rerank fallback：0。

人工严格答案检查为 10/15（66.7%）。h05、h06、h08 在完整证据已召回时错误拒答；h09、h15 的关键信息不完整。这说明 C1 减少了结构性引用错误，但拒答约束过于保守，不能据此宣称引用与整体生成质量达到 90%。

本轮没有填写完整的逐引用语义支持性 review 表，因此不能从“非法编号为 0”推导“严格引用准确率为 100%”。

原始 E2E JSON 生成后，使用以下命令生成人工判定模板并汇总预先约定的五项指标：

```powershell
python -m evaluation.review_e2e <result.json> --init <review.jsonl>
# 填写 answer_correct / citation_correct / 支持引用数 / refusal_correct / hallucination
python -m evaluation.review_e2e <result.json> --review <review.jsonl> --out <summary.json>
```

该 Holdout 已消费，不能作为下一轮 Prompt 调优集。若继续优化 C1，应使用 regression 或新增开发题，并在冻结新候选后建立新的盲测集。
