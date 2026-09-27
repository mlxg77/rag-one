# ADR-002：采用 `src/rag_one` 包布局

状态：已采用。

运行代码统一放入 `src/rag_one/`，按 ingestion、indexing、retrieval、generation 分责。脚本、评估、数据和文档放在包外。开发环境通过 `pip install -e .` 安装，不再依赖当前目录碰巧能导入 `src.*`。

结果是导入路径稳定、打包边界明确、测试可从任意工作目录执行。代价是本地开发必须先安装 editable 包；自动生成的 `*.egg-info` 不提交仓库。
