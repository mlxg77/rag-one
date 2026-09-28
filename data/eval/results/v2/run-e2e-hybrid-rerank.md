# 端到端评估报告：run-e2e-hybrid_rerank

## 文件说明

- v2.0 端到端评估 E4 链路报告；同名 `.json` 为权威原始数据，本报告为其渲染（本说明为归档补注）。
- 实验内容：hybrid + RRF + 重排 Top-5 + Qwen3-8B 生成。
- 实验角色：双链路对照最终链路（E4），与 E1 成对；结论见 `docs/reports/v2.0.md` 第 8 节。
- 生成与状态：2026-09-27 由 `evaluation/evaluate_e2e.py` 生成；属 v2.0 冻结快照。
- 读者：人读 md；程序经 `evaluation/review_e2e.py` 读同名 JSON。

## 运行信息

| 项 | 值 |
|---|---|
| 时间 | 2026-09-27T18:09:28 |
| 模式 | hybrid_rerank |
| 最终 Top-K | 5 |
| 题目数 / 参与统计 | 32 / 31（拒答题不计入） |
| 集合 / 向量数 | rag_mvp_docs / 111 |
| Embedding / LLM | BAAI/bge-m3 / Qwen/Qwen3-8B |

## 汇总指标

| 指标 | 值 | 说明 |
|---|---:|---|
| Recall@5（chunk 级） | 100.0% | 前 5 命中含任一相关块的题占比 |
| 相关块覆盖（Top-5） | 91.6% | 命中相关块数 / 标注总数 |
| Prompt tokens | avg 2425 / P50 2437 / P95 2523 | 生成请求输入 token（含 Top-5 上下文） |
| Completion tokens | avg 53 / P50 45 / P95 114 | 生成输出 token |
| 召回融合延迟 | P50 192 / P95 2282 ms | 双路召回 + RRF 融合（E4） |
| 重排延迟 | P50 755 / P95 1824 ms | Rerank API 逐对打分（E4） |
| 生成延迟 | P50 2496 / P95 6705 ms | LLM 答题 |
| 总延迟 | P50 3705 / P95 7817 ms | 单题端到端 |
| 重排输入 tokens | avg 9401 / P50 9580 | Rerank API 计费口径（E4） |
| 重排回退次数 | 0 | 失败回退 hybrid 的题数（应为 0） |

## 逐题明细

| 题 | 题型 | HitRank | 检索ms | 融合ms | 重排ms | 生成ms | 总ms | prompt_tok | completion_tok |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| q01 | direct | 1 | — | 1693 | 776 | 1933 | 4402 | 2523 | 31 |
| q02 | table | 1 | — | 200 | 888 | 1854 | 2942 | 2531 | 38 |
| q03 | confusable | 1 | — | 161 | 721 | 6705 | 7587 | 2484 | 37 |
| q04 | reasoning | 1 | — | 578 | 676 | 4987 | 6241 | 2423 | 48 |
| q05 | direct | 1 | — | 1176 | 624 | 5680 | 7480 | 2507 | 42 |
| q06 | direct | 1 | — | 2254 | 650 | 2447 | 5352 | 2437 | 53 |
| q07 | confusable | 1 | — | 1234 | 820 | 2552 | 4606 | 2426 | 62 |
| q08 | direct | 1 | — | 204 | 722 | 1939 | 2865 | 2438 | 39 |
| q09 | reasoning | 1 | — | 195 | 2471 | 2864 | 5530 | 2437 | 73 |
| q10 | direct | 1 | — | 2282 | 1097 | 4438 | 7817 | 2346 | 42 |
| q11 | multi_source | 1 | — | 2317 | 797 | 22958 | 26072 | 2359 | 66 |
| q12 | multi_source | 1 | — | 466 | 871 | 3070 | 4408 | 2410 | 70 |
| q13 | direct | 1 | — | 147 | 737 | 4435 | 5319 | 2388 | 114 |
| q14 | direct | 1 | — | 315 | 833 | 1555 | 2703 | 2388 | 27 |
| q15 | direct | 1 | — | 189 | 1824 | 1549 | 3562 | 2340 | 24 |
| q16 | multi_source | 1 | — | 184 | 731 | 5148 | 6062 | 2446 | 141 |
| q17 | multi_source | 1 | — | 348 | 686 | 4272 | 5306 | 2449 | 106 |
| q18 | trap | 1 | — | 192 | 690 | 3077 | 3959 | 2354 | 77 |
| q19 | trap | 1 | — | 161 | 779 | 2766 | 3705 | 2345 | 70 |
| q20 | confusable | 1 | — | 166 | 966 | 2859 | 3992 | 2469 | 49 |
| q21 | direct | 1 | — | 177 | 1060 | 1943 | 3180 | 2457 | 34 |
| q22 | unanswerable | 1 | — | 157 | 675 | 1111 | 1943 | 2439 | 6 |
| q23 | unanswerable | 1 | — | 261 | 649 | 2496 | 3406 | 2427 | 59 |
| q24 | unanswerable | — | — | 409 | 801 | 1729 | 2938 | 2483 | 30 |
| q25 | multi_source | 1 | — | 155 | 790 | 2660 | 3605 | 2377 | 57 |
| q26 | keyword | 1 | — | 203 | 662 | 2042 | 2906 | 2438 | 32 |
| q27 | keyword | 1 | — | 162 | 612 | 2347 | 3121 | 2440 | 55 |
| q28 | keyword | 1 | — | 156 | 581 | 1983 | 2721 | 2488 | 45 |
| q29 | keyword | 1 | — | 164 | 827 | 2433 | 3425 | 2342 | 41 |
| q30 | keyword | 1 | — | 177 | 755 | 1358 | 2290 | 2497 | 25 |
| q31 | confusable | 1 | — | 139 | 658 | 1723 | 2520 | 2393 | 29 |
| q32 | semantic | 1 | — | 160 | 762 | 2979 | 3902 | 2327 | 68 |

## 逐题答案与引用

### q01 [direct] HitRank=1

**问题**：普通员工去上海出差，酒店每晚含税最高可以报销多少？

**期望答案**：700 元。

**答案**：普通员工去上海出差，酒店每晚含税最高可以报销700元。  

使用的资料编号：[1]、[3]

**引用编号**：[1]、[3]

**命中**：1.✓ 10-faq.pdf:page-3:chunk-0 | 2.✓ 10-faq.pdf:page-1:chunk-0 | 3.✓ 06-travel-policy.md:chunk-0 | 4.✓ 06-travel-policy.md:chunk-4 | 5.✗ 06-travel-policy.md:chunk-5

### q02 [table] HitRank=1

**问题**：部门总监去成都出差的住宿标准是多少？

**期望答案**：每间夜含税最高 850 元。

**答案**：部门总监去成都出差的住宿标准是每间夜含税最高 850 元。

使用的资料编号：[1]、[2]、[3]。

**引用编号**：[1]、[2]、[3]

**命中**：1.✓ 10-faq.pdf:page-3:chunk-1 | 2.✓ 06-travel-policy.md:chunk-5 | 3.✓ 06-travel-policy.md:chunk-0 | 4.✗ 06-travel-policy.md:chunk-4 | 5.✗ 10-faq.pdf:page-3:chunk-0

### q03 [confusable] HitRank=1

**问题**：出差返回后多少天内要提交报销？

**期望答案**：返程之日起 15 个自然日内。

**答案**：根据差旅制度，差旅费用应在返程之日起 15 个自然日内提交。  

使用的资料编号：[1]、[2]、[3]

**引用编号**：[1]、[2]、[3]

**命中**：1.✓ 06-travel-policy.md:chunk-7 | 2.✓ 06-travel-policy.md:chunk-0 | 3.✓ 10-faq.pdf:page-3:chunk-0 | 4.✓ 10-faq.pdf:page-1:chunk-0 | 5.✗ 05-expense-policy.md:chunk-0

### q04 [reasoning] HitRank=1

**问题**：购买办公用品后 25 天还能正常提交报销吗？

**期望答案**：通常可以，日常费用应在发生之日起 30 个自然日内提交，但还要满足跨年度结账等要求。

**答案**：根据参考资料，日常费用应在费用发生之日起 30 个自然日内提交。因此，购买办公用品后 25 天仍然在规定的提交期限内，可以正常提交报销。

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 05-expense-policy.md:chunk-0 | 2.✗ 05-expense-policy.md:chunk-1 | 3.✗ 05-expense-policy.md:chunk-7 | 4.✓ 10-faq.pdf:page-2:chunk-1 | 5.✗ 05-expense-policy.md:chunk-8

### q05 [direct] HitRank=1

**问题**：一笔 6000 元的日常费用需要谁审批？

**期望答案**：需要直属经理、部门负责人和财务负责人审批。

**答案**：一笔 6000 元的日常费用需要直属经理、部门负责人和财务负责人共同审批。

使用的资料编号：[1]、[2]、[4]、[5]

**引用编号**：[1]、[2]、[4]、[5]

**命中**：1.✓ 05-expense-policy.md:chunk-5 | 2.✓ 05-expense-policy.md:chunk-0 | 3.✗ 10-faq.pdf:page-3:chunk-0 | 4.✗ 05-expense-policy.md:chunk-1 | 5.✗ 05-expense-policy.md:chunk-4

### q06 [direct] HitRank=1

**问题**：同一项采购能否拆成两笔来降低审批等级？

**期望答案**：不能。制度明确禁止为降低审批等级拆分同一项采购。

**答案**：根据参考资料，同一项采购不得拆成多笔以降低审批等级。金额判断以单笔交易为准，不得为了降低审批等级而人为拆分同一项采购。  

使用的资料编号：[1]、[2]、[4]

**引用编号**：[1]、[2]、[4]

**命中**：1.✓ 05-expense-policy.md:chunk-6 | 2.✓ 05-expense-policy.md:chunk-0 | 3.✗ 05-expense-policy.md:chunk-5 | 4.✗ 05-expense-policy.md:chunk-7 | 5.✗ 05-expense-policy.md:chunk-4

### q07 [confusable] HitRank=1

**问题**：连续请两天病假一定要医疗证明吗？

**期望答案**：通常不需要；连续病假达到三个工作日或以上才需要医疗机构证明。

**答案**：根据参考资料，连续病假不超过两个原本应工作的工作日时通常无需医疗证明；连续病假达到三个工作日或以上时，应提供由合法医疗机构出具的证明。因此，连续请两天病假通常不需要医疗证明。

使用的资料编号：[1]、[2]

**引用编号**：[1]、[2]

**命中**：1.✓ 04-leave-policy.md:chunk-4 | 2.✓ 04-leave-policy.md:chunk-0 | 3.✗ 04-leave-policy.md:chunk-5 | 4.✗ 04-leave-policy.md:chunk-8 | 5.✗ 04-leave-policy.md:chunk-2

### q08 [direct] HitRank=1

**问题**：连续休四天年假要提前多久申请？

**期望答案**：至少提前十个工作日。

**答案**：根据参考资料，连续休三天及以上年假应至少提前十个工作日申请。因此，连续休四天年假也应至少提前十个工作日申请。

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 04-leave-policy.md:chunk-0 | 2.✓ 04-leave-policy.md:chunk-2 | 3.✗ 04-leave-policy.md:chunk-6 | 4.✗ 04-leave-policy.md:chunk-7 | 5.✗ 04-leave-policy.md:chunk-5

### q09 [reasoning] HitRank=1

**问题**：员工周一周二休年假，周三生病，可以直接把原申请延长吗？

**期望答案**：不能直接混在原申请中，应当为周三单独申请病假，并联系经理处理。

**答案**：根据参考资料，员工周一周二休年假，周三生病，不能直接把原申请延长。年假与病假相邻时应分别申请，例如周一至周二年假已批准，周三因病无法工作，应单独提交病假申请，不得直接延长原年假申请。

使用的资料编号：[1]、[3]

**引用编号**：[1]、[3]

**命中**：1.✓ 04-leave-policy.md:chunk-7 | 2.✓ 04-leave-policy.md:chunk-1 | 3.✓ 04-leave-policy.md:chunk-0 | 4.✗ 04-leave-policy.md:chunk-3 | 5.✗ 10-faq.pdf:page-2:chunk-1

### q10 [direct] HitRank=1

**问题**：正式员工一周最多可以远程办公几天？

**期望答案**：经直属经理同意，每周最多两天。

**答案**：正式员工一周最多可以远程办公两天。未使用的天数不能跨周累计，也不能兑换成年假或调休。

使用的资料编号：[1]、[2]、[3]

**引用编号**：[1]、[2]、[3]

**命中**：1.✓ 10-faq.pdf:page-2:chunk-0 | 2.✓ 10-faq.pdf:page-1:chunk-0 | 3.✓ 07-remote-work.md:chunk-0 | 4.✓ 07-remote-work.md:chunk-1 | 5.✓ 10-faq.pdf:page-2:chunk-1

### q11 [multi_source] HitRank=1

**问题**：试用期员工是否也能每周远程办公两天？

**期望答案**：不能。试用期员工每次都要经理批准，并且每周最多一天。

**答案**：试用期员工不能每周远程办公两天。根据规定，试用期员工每次远程办公均须提前获得直属经理批准，并且每周最多一天。正式员工通过试用期后，才适用每周最多两天的远程办公规则。

使用的资料编号：[2]、[4]、[5]

**引用编号**：[2]、[4]、[5]

**命中**：1.✓ 10-faq.pdf:page-2:chunk-0 | 2.✓ 07-remote-work.md:chunk-0 | 3.✓ 10-faq.pdf:page-2:chunk-1 | 4.✗ 07-remote-work.md:chunk-1 | 5.✓ 07-remote-work.md:chunk-2

### q12 [multi_source] HitRank=1

**问题**：上周没有远程办公，这周能申请四天吗？

**期望答案**：不能，远程办公天数不能跨周累计；正式员工每周最多两天。

**答案**：根据参考资料，正式员工每周最多可以远程办公两天，未使用的天数不能跨周累计，也不能兑换成年假或调休。因此，上周未使用的远程办公天数不能留到下周使用，这周也不能申请四天远程办公。

使用的资料编号：[1]、[3]、[4]。

**引用编号**：[1]、[3]、[4]

**命中**：1.✓ 07-remote-work.md:chunk-2 | 2.✓ 10-faq.pdf:page-1:chunk-0 | 3.✓ 07-remote-work.md:chunk-0 | 4.✓ 10-faq.pdf:page-2:chunk-0 | 5.✗ 03-attendance.md:chunk-1

### q13 [direct] HitRank=1

**问题**：从另一个城市连续远程工作六个工作日，需要哪些批准？

**期望答案**：需要直属经理、人力资源和信息安全部门的书面批准。

**答案**：根据参考资料，从另一个城市连续远程工作六个工作日属于“异地长期远程办公”的情况。根据[1]和[3]的内容，计划连续五个工作日以上从其他城市或境外工作，必须提前取得直属经理、人力资源及信息安全部门的书面批准。

因此，从另一个城市连续远程工作六个工作日，需要以下批准：
- 直属经理的书面批准
- 人力资源部门的书面批准
- 信息安全部门的书面批准

使用的资料编号：[1]、[3]

**引用编号**：[1]、[3]

**命中**：1.✓ 07-remote-work.md:chunk-1 | 2.✓ 07-remote-work.md:chunk-7 | 3.✓ 07-remote-work.md:chunk-0 | 4.✗ 10-faq.pdf:page-2:chunk-0 | 5.✗ 10-faq.pdf:page-2:chunk-1

### q14 [direct] HitRank=1

**问题**：新员工需要在多久内开启多因素认证？

**期望答案**：领取电脑后的 24 小时内。

**答案**：新员工需要在领取电脑后的24小时内开启多因素认证。  

使用的资料编号：[1]、[2]

**引用编号**：[1]、[2]

**命中**：1.✓ 02-onboarding.md:chunk-4 | 2.✓ 02-onboarding.md:chunk-0 | 3.✗ 08-information-security.md:chunk-3 | 4.✗ 08-information-security.md:chunk-4 | 5.✗ 08-information-security.md:chunk-0

### q15 [direct] HitRank=1

**问题**：信息安全基础课程考试多少分算通过？

**期望答案**：80 分。

**答案**：信息安全基础课程考试达到 80 分方为通过。

使用的资料编号：[1]、[3]

**引用编号**：[1]、[3]

**命中**：1.✓ 02-onboarding.md:chunk-6 | 2.✓ 02-onboarding.md:chunk-0 | 3.✓ 02-onboarding.md:chunk-1 | 4.✗ 02-onboarding.md:chunk-3 | 5.✗ 01-company-overview.md:chunk-6

### q16 [multi_source] HitRank=1

**问题**：公司电脑丢失应该只提交 IT 工单吗？

**期望答案**：不应该。设备丢失属于安全事件，必须立即联系信息安全团队；紧急情况还要拨打 6110。

**答案**：根据参考资料，公司电脑丢失不应只提交 IT 工单。根据《信息安全规范》（参考资料 [2]），公司设备丢失属于需要立即报告的安全事件，应联系信息安全团队，而不是等到次日上班或只提交普通 IT 工单。此外，参考资料 [1] 也提到，远程办公期间发现公司设备丢失，应立即联系信息安全团队，不能等到次日上班或只提交普通 IT 工单。

因此，公司电脑丢失应通过安全报告渠道（如 `security@example.test` 或拨打内部电话 6110）进行报告，而不是仅提交 IT 工单。

使用的资料编号：[1]、[2]

**引用编号**：[2]、[1]

**命中**：1.✓ 07-remote-work.md:chunk-7 | 2.✓ 08-information-security.md:chunk-0 | 3.✗ 08-information-security.md:chunk-1 | 4.✓ 09-it-support.md:chunk-0 | 5.✗ 01-company-overview.md:chunk-6

### q17 [multi_source] HitRank=1

**问题**：收到索要验证码的邮件但没有点击，该怎么办？

**期望答案**：不要回复、点击或下载，应使用邮件客户端的“报告钓鱼”功能。

**答案**：收到索要验证码的邮件但没有点击，应使用邮件客户端中的“报告钓鱼”功能，让安全团队进行判断。即使没有点击，也应避免回复、下载或继续操作。此外，应确认事项的适用对象、起算时间、提交渠道和审批角色，并一次性提供足够判断的信息。如果后续发现日期、地点、金额、人员或业务目的发生实质变化，应重新确认原批准是否有效。

使用的资料编号：[1]、[2]、[3]

**引用编号**：[1]、[2]、[3]

**命中**：1.✓ 08-information-security.md:chunk-0 | 2.✓ 10-faq.pdf:page-4:chunk-0 | 3.✓ 08-information-security.md:chunk-5 | 4.✓ 10-faq.pdf:page-1:chunk-0 | 5.✗ 02-onboarding.md:chunk-3

### q18 [trap] HitRank=1

**问题**：P1 IT 故障承诺多久解决？

**期望答案**：手册只规定目标为 30 分钟内响应，不承诺在 30 分钟内解决。

**答案**：根据参考资料，P1 的目标是 30 分钟内响应，即开始处理或联系申请人，而不是承诺在 30 分钟内彻底解决。因此，P1 IT 故障并不承诺在特定时间内解决，仅保证在 30 分钟内开始处理。

使用的资料编号：[1]、[2]、[5]

**引用编号**：[1]、[2]、[5]

**命中**：1.✓ 10-faq.pdf:page-4:chunk-1 | 2.✓ 09-it-support.md:chunk-3 | 3.✓ 09-it-support.md:chunk-0 | 4.✗ 09-it-support.md:chunk-2 | 5.✓ 09-it-support.md:chunk-5

### q19 [trap] HitRank=1

**问题**：公司电脑用了四年后是否一定自动换新？

**期望答案**：不一定。四年时只是评估更新需求，由 IT 根据设备状况决定维修或更换。

**答案**：根据现有资料无法确定。  
参考资料中提到公司电脑“原则上每四年评估一次更新需求，但并非满四年自动换新”，这意味着是否换新取决于IT部门的评估结果，而不是自动进行。因此，不能确定公司电脑用了四年后是否一定自动换新。

使用的资料编号：[1]、[2]

**引用编号**：[1]、[2]

**命中**：1.✓ 09-it-support.md:chunk-6 | 2.✓ 09-it-support.md:chunk-0 | 3.✗ 08-information-security.md:chunk-4 | 4.✗ 10-faq.pdf:page-4:chunk-1 | 5.✗ 02-onboarding.md:chunk-3

### q20 [confusable] HitRank=1

**问题**：外出拜访客户会占用每周远程办公天数吗？

**期望答案**：不会，外勤不属于远程办公。

**答案**：根据参考资料，外出拜访客户属于外勤，而外勤不是远程办公，因此不占用每周远程办公天数。

使用的资料编号：[1]、[2]、[3]、[4]、[5]

**引用编号**：[1]、[2]、[3]、[4]、[5]

**命中**：1.✓ 03-attendance.md:chunk-1 | 2.✗ 03-attendance.md:chunk-0 | 3.✓ 03-attendance.md:chunk-7 | 4.✗ 10-faq.pdf:page-2:chunk-0 | 5.✗ 07-remote-work.md:chunk-0

### q21 [direct] HitRank=1

**问题**：考勤记录错了，应在多久内申请更正？

**期望答案**：三个工作日内。

**答案**：根据现有资料，考勤记录错了，应在三个工作日内提交更正申请。  

使用的资料编号：[1]、[2]、[4]

**引用编号**：[1]、[2]、[4]

**命中**：1.✓ 03-attendance.md:chunk-4 | 2.✓ 03-attendance.md:chunk-0 | 3.✗ 03-attendance.md:chunk-3 | 4.✗ 03-attendance.md:chunk-2 | 5.✗ 03-attendance.md:chunk-6

### q22 [unanswerable] HitRank=1

**问题**：公司每个月提供多少健身补贴？

**期望答案**：现有资料没有规定健身补贴金额，应向人力资源部门确认。

**答案**：根据现有资料无法确定。

**引用编号**：（无）

**命中**：1.✓ 10-faq.pdf:page-1:chunk-0 | 2.✓ 10-faq.pdf:page-4:chunk-0 | 3.✗ 06-travel-policy.md:chunk-5 | 4.✗ 01-company-overview.md:chunk-1 | 5.✗ 03-attendance.md:chunk-1

### q23 [unanswerable] HitRank=1

**问题**：杭州办公室的员工婚假统一是几天？

**期望答案**：资料没有给出固定天数，应根据工作地点适用规定向人力资源部门确认。

**答案**：根据现有资料无法确定。婚假的具体天数根据员工工作地点适用的法律和公司所在地政策执行，员工应向人力资源部门确认具体天数和材料。

使用的资料编号：[1]、[2]、[3]、[4]、[5]

**引用编号**：[1]、[2]、[3]、[4]、[5]

**命中**：1.✓ 10-faq.pdf:page-5:chunk-0 | 2.✓ 04-leave-policy.md:chunk-6 | 3.✗ 10-faq.pdf:page-1:chunk-0 | 4.✓ 04-leave-policy.md:chunk-0 | 5.✗ 10-faq.pdf:page-2:chunk-0

### q24 [unanswerable] HitRank=—

**问题**：公司食堂午餐多少钱？

**期望答案**：现有资料没有提供公司食堂或午餐价格信息。

**答案**：根据现有资料无法确定。  
使用的资料编号：[1]、[2]、[3]、[4]、[5]

**引用编号**：[1]、[2]、[3]、[4]、[5]

**命中**：1.✗ 05-expense-policy.md:chunk-0 | 2.✗ 06-travel-policy.md:chunk-5 | 3.✗ 10-faq.pdf:page-3:chunk-1 | 4.✗ 05-expense-policy.md:chunk-1 | 5.✗ 06-travel-policy.md:chunk-0

### q25 [multi_source] HitRank=1

**问题**：客户数据可以保存在私人网盘吗？

**期望答案**：不可以，客户资料和工作文件不得保存在私人网盘，应使用公司批准的系统。

**答案**：根据参考资料，客户数据不得下载到个人设备，工作文件不得通过私人云盘或个人邮箱传输。因此，客户数据不可以保存在私人网盘。

使用的资料编号：[1]、[2]、[3]、[4]、[5]

**引用编号**：[1]、[2]、[3]、[4]、[5]

**命中**：1.✓ 01-company-overview.md:chunk-0 | 2.✓ 01-company-overview.md:chunk-5 | 3.✓ 01-company-overview.md:chunk-6 | 4.✓ 07-remote-work.md:chunk-6 | 5.✗ 09-it-support.md:chunk-7

### q26 [keyword] HitRank=1

**问题**：公司账户被锁定、无法登录系统提交工单时，可以拨打哪个内部电话？

**期望答案**：内部电话 6100。

**答案**：当公司账户被锁定且无法登录系统提交工单时，可以拨打内部电话 6100。  

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 09-it-support.md:chunk-0 | 2.✓ 09-it-support.md:chunk-2 | 3.✗ 08-information-security.md:chunk-0 | 4.✗ 01-company-overview.md:chunk-0 | 5.✗ 08-information-security.md:chunk-7

### q27 [keyword] HitRank=1

**问题**：发现公司电脑疑似感染恶意软件，应把安全事件报告发送到哪个邮箱？

**期望答案**：security@example.test；紧急情况还应拨打内部电话 6110。

**答案**：发现公司电脑疑似感染恶意软件，应把安全事件报告发送到 `security@example.test` 邮箱。紧急情况还应同时拨打内部电话 6110。

使用的资料编号：[1]、[2]、[3]。

**引用编号**：[1]、[2]、[3]

**命中**：1.✓ 08-information-security.md:chunk-7 | 2.✓ 08-information-security.md:chunk-6 | 3.✓ 08-information-security.md:chunk-0 | 4.✓ 09-it-support.md:chunk-0 | 5.✗ 08-information-security.md:chunk-1

### q28 [keyword] HitRank=1

**问题**：安装新软件、打印机故障这类普通技术问题，应通过哪个系统的什么项目提交工单？

**期望答案**：通过 Orbit 的“IT 服务台”项目提交工单。

**答案**：安装新软件、打印机故障这类普通技术问题，应通过 Orbit 的“IT 服务台”项目提交工单。

使用的资料编号：[1]、[2]、[4]、[5]

**引用编号**：[1]、[2]、[4]、[5]

**命中**：1.✓ 09-it-support.md:chunk-0 | 2.✓ 09-it-support.md:chunk-1 | 3.✗ 08-information-security.md:chunk-1 | 4.✓ 01-company-overview.md:chunk-0 | 5.✗ 08-information-security.md:chunk-0

### q29 [keyword] HitRank=1

**问题**：P2 工单的目标响应时间是多久？

**期望答案**：2 个工作小时内响应。

**答案**：P2 工单的目标响应时间是两个工作小时内。  
响应时间是指 IT 开始处理或联系申请人的时间，而不是承诺在该时间内彻底解决问题。

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 09-it-support.md:chunk-0 | 2.✓ 09-it-support.md:chunk-3 | 3.✗ 09-it-support.md:chunk-5 | 4.✗ 10-faq.pdf:page-1:chunk-0 | 5.✗ 10-faq.pdf:page-4:chunk-1

### q30 [keyword] HitRank=1

**问题**：按公司数据分类标准，“完整客户数据导出”属于哪一级？

**期望答案**：严格机密。严格机密信息包括生产系统密钥、完整客户数据导出和并购材料。

**答案**：根据公司数据分类标准，“完整客户数据导出”属于严格机密信息。

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 08-information-security.md:chunk-0 | 2.✓ 08-information-security.md:chunk-3 | 3.✓ 08-information-security.md:chunk-2 | 4.✗ 09-it-support.md:chunk-3 | 5.✗ 02-onboarding.md:chunk-5

### q31 [confusable] HitRank=1

**问题**：杭州总部前台在工作日的开放时间是什么？

**期望答案**：08:30—18:30。

**答案**：杭州总部前台在工作日的开放时间是08:30—18:30。

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 01-company-overview.md:chunk-2 | 2.✓ 01-company-overview.md:chunk-0 | 3.✗ 01-company-overview.md:chunk-3 | 4.✗ 01-company-overview.md:chunk-4 | 5.✗ 09-it-support.md:chunk-2

### q32 [semantic] HitRank=1

**问题**：台风导致地铁停运，今天能临时申请在家办公吗？

**期望答案**：可以当日联系经理处理；一般情况下最晚应在计划日前一个工作日的 16:00 前通过团队日历提交申请。

**答案**：根据参考资料，台风导致地铁停运属于恶劣天气，可以当日联系经理处理临时申请。但临时申请仍需明确工作地点和可联系状态，不等于自动获得批准。因此，今天可以临时申请在家办公，但需与经理沟通并获得批准。

使用的资料编号：[1]、[3]

**引用编号**：[1]、[3]

**命中**：1.✓ 07-remote-work.md:chunk-4 | 2.✗ 07-remote-work.md:chunk-3 | 3.✓ 07-remote-work.md:chunk-0 | 4.✗ 10-faq.pdf:page-1:chunk-0 | 5.✗ 01-company-overview.md:chunk-6

