# 端到端评估报告：run-e2e-vector

## 运行信息

| 项 | 值 |
|---|---|
| 时间 | 2026-09-27T18:06:43 |
| 模式 | vector |
| 最终 Top-K | 5 |
| 题目数 / 参与统计 | 32 / 31（拒答题不计入） |
| 集合 / 向量数 | rag_mvp_docs / 111 |
| Embedding / LLM | BAAI/bge-m3 / Qwen/Qwen3-8B |

## 汇总指标

| 指标 | 值 | 说明 |
|---|---:|---|
| Recall@5（chunk 级） | 96.8% | 前 5 命中含任一相关块的题占比 |
| 相关块覆盖（Top-5） | 70.9% | 命中相关块数 / 标注总数 |
| Prompt tokens | avg 2368 / P50 2383 / P95 2503 | 生成请求输入 token（含 Top-5 上下文） |
| Completion tokens | avg 44 / P50 37 / P95 73 | 生成输出 token |
| 检索延迟 | P50 310 / P95 2615 ms | 查询向量化 + 向量库 Top-K（E1） |
| 生成延迟 | P50 2202 / P95 6347 ms | LLM 答题 |
| 总延迟 | P50 3204 / P95 8037 ms | 单题端到端 |

## 逐题明细

| 题 | 题型 | HitRank | 检索ms | 融合ms | 重排ms | 生成ms | 总ms | prompt_tok | completion_tok |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| q01 | direct | 2 | 1082 | — | — | 2202 | 3284 | 2503 | 32 |
| q02 | table | 1 | 2818 | — | — | 2705 | 5523 | 2515 | 37 |
| q03 | confusable | 2 | 1676 | — | — | 1740 | 3416 | 2461 | 24 |
| q04 | reasoning | 1 | 2572 | — | — | 2235 | 4808 | 2452 | 48 |
| q05 | direct | 1 | 1349 | — | — | 1854 | 3204 | 2405 | 38 |
| q06 | direct | 2 | 2615 | — | — | 2428 | 5043 | 2457 | 51 |
| q07 | confusable | 1 | 1984 | — | — | 1716 | 3700 | 2426 | 37 |
| q08 | direct | 1 | 232 | — | — | 2232 | 2464 | 2466 | 45 |
| q09 | reasoning | 1 | 848 | — | — | 4056 | 4904 | 2421 | 70 |
| q10 | direct | 1 | 946 | — | — | 1826 | 2772 | 2346 | 31 |
| q11 | multi_source | 1 | 191 | — | — | 4304 | 4495 | 2359 | 71 |
| q12 | multi_source | 1 | 179 | — | — | 2832 | 3011 | 2390 | 73 |
| q13 | direct | 1 | 168 | — | — | 2590 | 2757 | 2351 | 59 |
| q14 | direct | 2 | 2597 | — | — | 1977 | 4574 | 2343 | 26 |
| q15 | direct | 1 | 637 | — | — | 1671 | 2308 | 2342 | 27 |
| q16 | multi_source | 3 | 168 | — | — | 3155 | 3323 | 2497 | 58 |
| q17 | multi_source | 1 | 1383 | — | — | 4486 | 5868 | 2383 | 98 |
| q18 | trap | 1 | 170 | — | — | 7867 | 8037 | 2340 | 51 |
| q19 | trap | 1 | 989 | — | — | 3005 | 3994 | 2286 | 65 |
| q20 | confusable | — | 168 | — | — | 1975 | 2143 | 2322 | 41 |
| q21 | direct | 2 | 150 | — | — | 1726 | 1876 | 2064 | 30 |
| q22 | unanswerable | 1 | 168 | — | — | 854 | 1021 | 2279 | 6 |
| q23 | unanswerable | 1 | 729 | — | — | 1631 | 2359 | 2422 | 29 |
| q24 | unanswerable | — | 151 | — | — | 1498 | 1650 | 2440 | 30 |
| q25 | multi_source | 1 | 151 | — | — | 2689 | 2840 | 2412 | 68 |
| q26 | keyword | 1 | 166 | — | — | 1892 | 2058 | 2338 | 37 |
| q27 | keyword | 1 | 1841 | — | — | 1845 | 3687 | 2326 | 33 |
| q28 | keyword | 1 | 2357 | — | — | 6347 | 8705 | 2344 | 33 |
| q29 | keyword | 1 | 310 | — | — | 4514 | 4824 | 2415 | 29 |
| q30 | keyword | 1 | 167 | — | — | 1666 | 1834 | 1959 | 24 |
| q31 | confusable | 2 | 174 | — | — | 1612 | 1787 | 2393 | 30 |
| q32 | semantic | 2 | 151 | — | — | 2812 | 2963 | 2305 | 66 |

## 逐题答案与引用

### q01 [direct] HitRank=2

**问题**：普通员工去上海出差，酒店每晚含税最高可以报销多少？

**期望答案**：700 元。

**答案**：普通员工去上海出差，酒店每晚含税最高可以报销 700 元。

使用的资料编号：[1]、[3]

**引用编号**：[1]、[3]

**命中**：1.✗ 06-travel-policy.md:chunk-5 | 2.✓ 10-faq.pdf:page-3:chunk-0 | 3.✓ 06-travel-policy.md:chunk-0 | 4.✓ 10-faq.pdf:page-1:chunk-0 | 5.✗ 05-expense-policy.md:chunk-0

### q02 [table] HitRank=1

**问题**：部门总监去成都出差的住宿标准是多少？

**期望答案**：每间夜含税最高 850 元。

**答案**：部门总监去成都出差的住宿标准是每间夜含税最高 850 元。

使用的资料编号：[1]、[2]、[3]

**引用编号**：[1]、[2]、[3]

**命中**：1.✓ 10-faq.pdf:page-3:chunk-1 | 2.✓ 06-travel-policy.md:chunk-5 | 3.✓ 06-travel-policy.md:chunk-0 | 4.✗ 06-travel-policy.md:chunk-4 | 5.✗ 01-company-overview.md:chunk-4

### q03 [confusable] HitRank=2

**问题**：出差返回后多少天内要提交报销？

**期望答案**：返程之日起 15 个自然日内。

**答案**：差旅费用应在返程之日起 15 个自然日内提交。  

使用的资料编号：[3]

**引用编号**：[3]

**命中**：1.✗ 05-expense-policy.md:chunk-0 | 2.✓ 06-travel-policy.md:chunk-7 | 3.✓ 06-travel-policy.md:chunk-0 | 4.✗ 05-expense-policy.md:chunk-1 | 5.✓ 10-faq.pdf:page-1:chunk-0

### q04 [reasoning] HitRank=1

**问题**：购买办公用品后 25 天还能正常提交报销吗？

**期望答案**：通常可以，日常费用应在发生之日起 30 个自然日内提交，但还要满足跨年度结账等要求。

**答案**：根据参考资料，日常费用应在费用发生之日起 30 个自然日内提交。因此，购买办公用品后 25 天仍然在规定的提交期限内，可以正常提交报销。

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 05-expense-policy.md:chunk-0 | 2.✗ 05-expense-policy.md:chunk-1 | 3.✗ 05-expense-policy.md:chunk-7 | 4.✓ 10-faq.pdf:page-1:chunk-0 | 5.✗ 05-expense-policy.md:chunk-8

### q05 [direct] HitRank=1

**问题**：一笔 6000 元的日常费用需要谁审批？

**期望答案**：需要直属经理、部门负责人和财务负责人审批。

**答案**：一笔 6000 元的日常费用需要直属经理、部门负责人和财务负责人共同审批。

使用的资料编号：[1]、[2]、[4]

**引用编号**：[1]、[2]、[4]

**命中**：1.✓ 05-expense-policy.md:chunk-5 | 2.✓ 05-expense-policy.md:chunk-0 | 3.✗ 05-expense-policy.md:chunk-4 | 4.✗ 05-expense-policy.md:chunk-2 | 5.✗ 10-faq.pdf:page-3:chunk-1

### q06 [direct] HitRank=2

**问题**：同一项采购能否拆成两笔来降低审批等级？

**期望答案**：不能。制度明确禁止为降低审批等级拆分同一项采购。

**答案**：根据参考资料，同一项采购不得拆成多笔来降低审批等级。这是为了防止通过拆分交易规避原规则，确保审批流程的合规性和透明度。

使用的资料编号：[1]、[2]、[3]

**引用编号**：[1]、[2]、[3]

**命中**：1.✗ 05-expense-policy.md:chunk-5 | 2.✓ 05-expense-policy.md:chunk-6 | 3.✗ 05-expense-policy.md:chunk-4 | 4.✗ 08-information-security.md:chunk-3 | 5.✗ 09-it-support.md:chunk-3

### q07 [confusable] HitRank=1

**问题**：连续请两天病假一定要医疗证明吗？

**期望答案**：通常不需要；连续病假达到三个工作日或以上才需要医疗机构证明。

**答案**：根据参考资料，连续病假不超过两个原本应工作的工作日时通常无需医疗证明。因此，连续请两天病假不需要医疗证明。

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 04-leave-policy.md:chunk-4 | 2.✗ 04-leave-policy.md:chunk-5 | 3.✓ 04-leave-policy.md:chunk-0 | 4.✗ 04-leave-policy.md:chunk-1 | 5.✗ 10-faq.pdf:page-1:chunk-0

### q08 [direct] HitRank=1

**问题**：连续休四天年假要提前多久申请？

**期望答案**：至少提前十个工作日。

**答案**：根据参考资料，连续休年假三天及以上，应至少提前十个工作日申请。因此，连续休四天年假也属于三天及以上的情况，应至少提前十个工作日申请。

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 04-leave-policy.md:chunk-0 | 2.✓ 04-leave-policy.md:chunk-2 | 3.✗ 04-leave-policy.md:chunk-1 | 4.✗ 04-leave-policy.md:chunk-5 | 5.✗ 04-leave-policy.md:chunk-3

### q09 [reasoning] HitRank=1

**问题**：员工周一周二休年假，周三生病，可以直接把原申请延长吗？

**期望答案**：不能直接混在原申请中，应当为周三单独申请病假，并联系经理处理。

**答案**：根据参考资料，员工周一周二休年假，周三生病，不能直接将原申请延长。年假和病假是两种不同的假期类型，如果年假与病假发生衔接，两类假期应分别提交申请。因此，员工周三因病无法工作，应单独申请病假。

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 04-leave-policy.md:chunk-0 | 2.✗ 04-leave-policy.md:chunk-5 | 3.✗ 10-faq.pdf:page-1:chunk-0 | 4.✗ 04-leave-policy.md:chunk-2 | 5.✗ 04-leave-policy.md:chunk-3

### q10 [direct] HitRank=1

**问题**：正式员工一周最多可以远程办公几天？

**期望答案**：经直属经理同意，每周最多两天。

**答案**：正式员工一周最多可以远程办公两天。未使用的天数不能跨周累计，也不能兑换为额外假期。

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 07-remote-work.md:chunk-0 | 2.✓ 10-faq.pdf:page-1:chunk-0 | 3.✓ 10-faq.pdf:page-2:chunk-0 | 4.✓ 07-remote-work.md:chunk-1 | 5.✓ 10-faq.pdf:page-2:chunk-1

### q11 [multi_source] HitRank=1

**问题**：试用期员工是否也能每周远程办公两天？

**期望答案**：不能。试用期员工每次都要经理批准，并且每周最多一天。

**答案**：根据参考资料，试用期员工原则上以办公室办公为主，每次远程办公均须提前取得直属经理批准，并且每周最多一天。试用期员工不能直接套用正式员工每周两天的规则。

因此，试用期员工每周远程办公两天是不被允许的。

使用的资料编号：[1]、[4]

**引用编号**：[1]、[4]

**命中**：1.✓ 07-remote-work.md:chunk-0 | 2.✓ 10-faq.pdf:page-2:chunk-1 | 3.✓ 10-faq.pdf:page-2:chunk-0 | 4.✓ 07-remote-work.md:chunk-2 | 5.✗ 07-remote-work.md:chunk-1

### q12 [multi_source] HitRank=1

**问题**：上周没有远程办公，这周能申请四天吗？

**期望答案**：不能，远程办公天数不能跨周累计；正式员工每周最多两天。

**答案**：根据现有资料无法确定。  
参考资料中提到，正式员工每周最多可以远程办公两天，且远程办公天数不能跨周累计。但未明确说明如果上周没有使用远程办公天数，是否可以申请更多天数。因此，无法确定是否可以申请四天远程办公。

使用的资料编号：[1]、[4]

**引用编号**：[1]、[4]

**命中**：1.✓ 07-remote-work.md:chunk-0 | 2.✓ 10-faq.pdf:page-1:chunk-0 | 3.✗ 07-remote-work.md:chunk-1 | 4.✓ 10-faq.pdf:page-2:chunk-0 | 5.✓ 07-remote-work.md:chunk-2

### q13 [direct] HitRank=1

**问题**：从另一个城市连续远程工作六个工作日，需要哪些批准？

**期望答案**：需要直属经理、人力资源和信息安全部门的书面批准。

**答案**：根据参考资料，从另一个城市连续远程工作六个工作日，属于计划连续五个工作日以上从其他城市或境外工作的情况，必须提前取得直属经理、人力资源及信息安全部门的书面批准。

使用的资料编号：[1]、[2]、[4]

**引用编号**：[1]、[2]、[4]

**命中**：1.✓ 07-remote-work.md:chunk-1 | 2.✓ 07-remote-work.md:chunk-0 | 3.✗ 10-faq.pdf:page-2:chunk-1 | 4.✗ 10-faq.pdf:page-2:chunk-0 | 5.✗ 10-faq.pdf:page-1:chunk-0

### q14 [direct] HitRank=2

**问题**：新员工需要在多久内开启多因素认证？

**期望答案**：领取电脑后的 24 小时内。

**答案**：新员工需要在领取电脑后的24小时内启用多因素认证。

使用的资料编号：[2]、[3]

**引用编号**：[2]、[3]

**命中**：1.✗ 08-information-security.md:chunk-4 | 2.✓ 02-onboarding.md:chunk-4 | 3.✓ 02-onboarding.md:chunk-0 | 4.✗ 02-onboarding.md:chunk-1 | 5.✗ 08-information-security.md:chunk-3

### q15 [direct] HitRank=1

**问题**：信息安全基础课程考试多少分算通过？

**期望答案**：80 分。

**答案**：信息安全基础课程考试达到 80 分算通过。

使用的资料编号：[1]、[2]、[4]

**引用编号**：[1]、[2]、[4]

**命中**：1.✓ 02-onboarding.md:chunk-6 | 2.✗ 08-information-security.md:chunk-0 | 3.✓ 02-onboarding.md:chunk-0 | 4.✓ 02-onboarding.md:chunk-1 | 5.✗ 01-company-overview.md:chunk-6

### q16 [multi_source] HitRank=3

**问题**：公司电脑丢失应该只提交 IT 工单吗？

**期望答案**：不应该。设备丢失属于安全事件，必须立即联系信息安全团队；紧急情况还要拨打 6110。

**答案**：根据参考资料，公司电脑丢失不应只提交 IT 工单。远程办公期间发现公司设备丢失，应立即联系信息安全团队，不能等到次日上班或只提交普通 IT 工单。应说明时间、地点和设备情况。

使用的资料编号：[5]

**引用编号**：[5]

**命中**：1.✗ 08-information-security.md:chunk-1 | 2.✗ 09-it-support.md:chunk-1 | 3.✓ 09-it-support.md:chunk-0 | 4.✗ 02-onboarding.md:chunk-3 | 5.✓ 07-remote-work.md:chunk-7

### q17 [multi_source] HitRank=1

**问题**：收到索要验证码的邮件但没有点击，该怎么办？

**期望答案**：不要回复、点击或下载，应使用邮件客户端的“报告钓鱼”功能。

**答案**：收到索要验证码的邮件但没有点击，应避免回复、下载或继续操作，并使用邮件客户端“报告钓鱼”功能，让安全团队开展判断。同时，应确认该邮件是否为可疑邮件，根据规则说明，索要验证码的异常邮件应谨慎处理，不要点击链接或打开附件。如果不确定邮件的合法性，应按照“识别可疑邮件”的规则进行处理。

使用的资料编号：[1]、[3]、[5]

**引用编号**：[1]、[3]、[5]

**命中**：1.✓ 10-faq.pdf:page-4:chunk-0 | 2.✗ 08-information-security.md:chunk-6 | 3.✓ 08-information-security.md:chunk-5 | 4.✗ 02-onboarding.md:chunk-4 | 5.✗ 08-information-security.md:chunk-4

### q18 [trap] HitRank=1

**问题**：P1 IT 故障承诺多久解决？

**期望答案**：手册只规定目标为 30 分钟内响应，不承诺在 30 分钟内解决。

**答案**：根据参考资料，P1 优先级的IT故障承诺在30分钟内响应，即开始处理或联系申请人，而不是承诺在30分钟内彻底解决。

使用的资料编号：[1]、[3]、[5]

**引用编号**：[1]、[3]、[5]

**命中**：1.✓ 09-it-support.md:chunk-0 | 2.✓ 09-it-support.md:chunk-3 | 3.✓ 10-faq.pdf:page-4:chunk-1 | 4.✗ 09-it-support.md:chunk-4 | 5.✓ 09-it-support.md:chunk-5

### q19 [trap] HitRank=1

**问题**：公司电脑用了四年后是否一定自动换新？

**期望答案**：不一定。四年时只是评估更新需求，由 IT 根据设备状况决定维修或更换。

**答案**：根据参考资料，公司电脑原则上每四年评估一次更新需求，但并非满四年自动换新。IT部门会根据损坏、性能、岗位需求和安全支持状态决定维修或更换。因此，公司电脑用了四年后不一定自动换新，需根据实际情况评估决定。

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 09-it-support.md:chunk-6 | 2.✗ 08-information-security.md:chunk-1 | 3.✗ 10-faq.pdf:page-4:chunk-1 | 4.✗ 02-onboarding.md:chunk-10 | 5.✗ 09-it-support.md:chunk-1

### q20 [confusable] HitRank=—

**问题**：外出拜访客户会占用每周远程办公天数吗？

**期望答案**：不会，外勤不属于远程办公。

**答案**：根据现有资料无法确定。参考资料中未提及外出拜访客户是否占用每周远程办公天数。  
使用的资料编号：[1]、[2]、[4]、[5]

**引用编号**：[1]、[2]、[4]、[5]

**命中**：1.✗ 10-faq.pdf:page-1:chunk-0 | 2.✗ 07-remote-work.md:chunk-0 | 3.✗ 10-faq.pdf:page-2:chunk-1 | 4.✗ 07-remote-work.md:chunk-2 | 5.✗ 10-faq.pdf:page-2:chunk-0

### q21 [direct] HitRank=2

**问题**：考勤记录错了，应在多久内申请更正？

**期望答案**：三个工作日内。

**答案**：根据现有资料，考勤记录错了，应在三个工作日内提交更正申请。  

使用的资料编号：[1]、[3]

**引用编号**：[1]、[3]

**命中**：1.✗ 03-attendance.md:chunk-3 | 2.✓ 03-attendance.md:chunk-4 | 3.✓ 03-attendance.md:chunk-0 | 4.✗ 04-leave-policy.md:chunk-10 | 5.✗ 05-expense-policy.md:chunk-10

### q22 [unanswerable] HitRank=1

**问题**：公司每个月提供多少健身补贴？

**期望答案**：现有资料没有规定健身补贴金额，应向人力资源部门确认。

**答案**：根据现有资料无法确定。

**引用编号**：（无）

**命中**：1.✓ 10-faq.pdf:page-1:chunk-0 | 2.✗ 05-expense-policy.md:chunk-0 | 3.✗ 05-expense-policy.md:chunk-1 | 4.✗ 02-onboarding.md:chunk-10 | 5.✗ 04-leave-policy.md:chunk-0

### q23 [unanswerable] HitRank=1

**问题**：杭州办公室的员工婚假统一是几天？

**期望答案**：资料没有给出固定天数，应根据工作地点适用规定向人力资源部门确认。

**答案**：根据现有资料无法确定。  
参考资料编号：[1]、[2]、[3]、[4]、[5]

**引用编号**：[1]、[2]、[3]、[4]、[5]

**命中**：1.✓ 04-leave-policy.md:chunk-0 | 2.✗ 10-faq.pdf:page-1:chunk-0 | 3.✓ 10-faq.pdf:page-5:chunk-0 | 4.✗ 01-company-overview.md:chunk-2 | 5.✗ 03-attendance.md:chunk-0

### q24 [unanswerable] HitRank=—

**问题**：公司食堂午餐多少钱？

**期望答案**：现有资料没有提供公司食堂或午餐价格信息。

**答案**：根据现有资料无法确定。  

使用的资料编号：[1]、[2]、[3]、[4]、[5]

**引用编号**：[1]、[2]、[3]、[4]、[5]

**命中**：1.✗ 05-expense-policy.md:chunk-0 | 2.✗ 06-travel-policy.md:chunk-0 | 3.✗ 03-attendance.md:chunk-0 | 4.✗ 10-faq.pdf:page-1:chunk-0 | 5.✗ 05-expense-policy.md:chunk-1

### q25 [multi_source] HitRank=1

**问题**：客户数据可以保存在私人网盘吗？

**期望答案**：不可以，客户资料和工作文件不得保存在私人网盘，应使用公司批准的系统。

**答案**：根据参考资料，客户数据不得保存在私人网盘。客户材料和内部文件必须进入公司批准的存储空间，私人网盘、个人邮箱和未经批准的同步工具不属于合规保存位置，即使是为了临时中转或在家继续工作也不例外。

使用的资料编号：[1]、[3]、[4]

**引用编号**：[1]、[3]、[4]

**命中**：1.✓ 01-company-overview.md:chunk-6 | 2.✓ 01-company-overview.md:chunk-5 | 3.✗ 08-information-security.md:chunk-0 | 4.✓ 07-remote-work.md:chunk-6 | 5.✗ 08-information-security.md:chunk-1

### q26 [keyword] HitRank=1

**问题**：公司账户被锁定、无法登录系统提交工单时，可以拨打哪个内部电话？

**期望答案**：内部电话 6100。

**答案**：当公司账户被锁定且无法登录系统提交工单时，可以拨打内部电话 **6100**。  

使用的资料编号：[1]、[2]

**引用编号**：[1]、[2]

**命中**：1.✓ 09-it-support.md:chunk-2 | 2.✓ 09-it-support.md:chunk-0 | 3.✗ 02-onboarding.md:chunk-10 | 4.✗ 08-information-security.md:chunk-7 | 5.✗ 08-information-security.md:chunk-0

### q27 [keyword] HitRank=1

**问题**：发现公司电脑疑似感染恶意软件，应把安全事件报告发送到哪个邮箱？

**期望答案**：security@example.test；紧急情况还应拨打内部电话 6110。

**答案**：发现公司电脑疑似感染恶意软件，应把安全事件报告发送到 `security@example.test` 邮箱。  
使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 08-information-security.md:chunk-0 | 2.✓ 08-information-security.md:chunk-7 | 3.✗ 01-company-overview.md:chunk-6 | 4.✗ 10-faq.pdf:page-4:chunk-0 | 5.✗ 02-onboarding.md:chunk-10

### q28 [keyword] HitRank=1

**问题**：安装新软件、打印机故障这类普通技术问题，应通过哪个系统的什么项目提交工单？

**期望答案**：通过 Orbit 的“IT 服务台”项目提交工单。

**答案**：安装新软件、打印机故障这类普通技术问题，应通过 Orbit 的“IT 服务台”项目提交工单。

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 09-it-support.md:chunk-0 | 2.✗ 08-information-security.md:chunk-1 | 3.✗ 02-onboarding.md:chunk-10 | 4.✗ 08-information-security.md:chunk-8 | 5.✓ 09-it-support.md:chunk-1

### q29 [keyword] HitRank=1

**问题**：P2 工单的目标响应时间是多久？

**期望答案**：2 个工作小时内响应。

**答案**：P2 工单的目标响应时间是两个工作小时内。  

使用的资料编号：[1]、[3]、[5]

**引用编号**：[1]、[3]、[5]

**命中**：1.✓ 09-it-support.md:chunk-3 | 2.✗ 09-it-support.md:chunk-4 | 3.✓ 09-it-support.md:chunk-0 | 4.✗ 09-it-support.md:chunk-2 | 5.✗ 09-it-support.md:chunk-5

### q30 [keyword] HitRank=1

**问题**：按公司数据分类标准，“完整客户数据导出”属于哪一级？

**期望答案**：严格机密。严格机密信息包括生产系统密钥、完整客户数据导出和并购材料。

**答案**：根据参考资料，"完整客户数据导出"属于严格机密信息。  

使用的资料编号：[1]

**引用编号**：[1]

**命中**：1.✓ 08-information-security.md:chunk-0 | 2.✗ 02-onboarding.md:chunk-10 | 3.✗ 09-it-support.md:chunk-3 | 4.✗ 09-it-support.md:chunk-10 | 5.✗ 08-information-security.md:chunk-10

### q31 [confusable] HitRank=2

**问题**：杭州总部前台在工作日的开放时间是什么？

**期望答案**：08:30—18:30。

**答案**：杭州总部前台在工作日的开放时间是 08:30—18:30。

使用的资料编号：[3]

**引用编号**：[3]

**命中**：1.✗ 01-company-overview.md:chunk-3 | 2.✓ 01-company-overview.md:chunk-2 | 3.✓ 01-company-overview.md:chunk-0 | 4.✗ 01-company-overview.md:chunk-4 | 5.✗ 09-it-support.md:chunk-2

### q32 [semantic] HitRank=2

**问题**：台风导致地铁停运，今天能临时申请在家办公吗？

**期望答案**：可以当日联系经理处理；一般情况下最晚应在计划日前一个工作日的 16:00 前通过团队日历提交申请。

**答案**：根据台风导致地铁停运的情况，员工可以临时申请在家办公。这种情况下属于“临时天气例外”，可以在当日联系经理处理。临时申请仍需明确工作地点和可联系状态，但不等于自动获得批准。经理将根据实际情况判断是否批准远程办公。  

使用的资料编号：[2]

**引用编号**：[2]

**命中**：1.✗ 10-faq.pdf:page-1:chunk-0 | 2.✓ 07-remote-work.md:chunk-0 | 3.✓ 07-remote-work.md:chunk-4 | 4.✗ 07-remote-work.md:chunk-3 | 5.✗ 01-company-overview.md:chunk-3

