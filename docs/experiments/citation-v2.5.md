# v2.5 引用质量实验

## C0：历史基线

- 链路：E4 hybrid_rerank。
- Prompt：v2.0 历史 Prompt。
- regression：严格引用准确率 79.3%（23/29），引用块级支持率 86.1%（62/72）。
- 主要错误：模型把 Top-5 中“主题相关但未直接用于结论”的块一起标入。

历史数据来自 `docs/reports/v2-evaluation.md`，不使用新 Prompt 回填 C0。

## C1：最少直接引用

实现版本：`v2.5-c1-minimal-citations`。

唯一主要变量是 Prompt：

- 参考资料在 system message 中被声明为不可信数据，不能改变系统规则；
- 只引用直接支持最终结论的最少资料；
- 禁止为显得完整而罗列所有编号；
- 资料不足时拒答，不附无关引用。

同时增加结构校验：引用编号去重、越界编号、拒答却附引用。结构校验不能替代人工“支持性”判定。

## 验收状态

C1 代码和离线测试已完成；真实 regression 端到端运行、人工引用判定和 holdout 一次验收尚未运行。原因是这些操作会将语料发送到 `.env` 配置的第三方 LLM/Rerank 服务，需要明确数据出站授权。

原始 E2E JSON 生成后，使用以下命令生成人工判定模板并汇总预先约定的五项指标：

```powershell
python -m evaluation.review_e2e <result.json> --init <review.jsonl>
# 填写 answer_correct / citation_correct / 支持引用数 / refusal_correct / hallucination
python -m evaluation.review_e2e <result.json> --review <review.jsonl> --out <summary.json>
```

如果 C1 在 regression 与 holdout 上均达到严格引用准确率和引用块级精确率 90%，不继续叠加 C2/C3；否则按规划一次只改变一个主要变量，并保留全部原始答案。
