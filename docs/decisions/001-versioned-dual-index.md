# ADR-001：不可变双索引版本与原子 active pointer

状态：已采用。

## 背景

v2.0 的向量 staging 集合改名与 BM25 文件替换是两个发布动作。即使各自动作安全，两者之间仍可能出现向量已新、BM25 仍旧的混合状态；删除旧集合再改名也会缩小回滚空间。

## 决定

每次构建生成唯一版本。该版本同时包含 Chroma collection、BM25 JSON 与 manifest。只有 Embedding、两套写入、条数、ID 集合和可查询性全部通过后，才使用 `os.replace` 原子替换 `storage/active-index.json`。

读取端先读 active manifest，再从同一 manifest 取得向量集合与 BM25 文件。旧版本不在发布流程中删除，回滚只是重新激活旧 manifest。

## 后果

- 任一构建步骤失败不会破坏 active version。
- pointer 替换失败时保留完整候选版本，便于诊断或稍后激活。
- 本地存储会累积旧版本，需要未来提供独立、保留至少一个回滚版本的清理命令。
- 多进程同时发布时仍是“最后一次原子替换获胜”；当前单机学习项目不实现分布式锁。
