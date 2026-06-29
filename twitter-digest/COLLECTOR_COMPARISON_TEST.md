# X/Twitter Collector Comparison Test Plan

## 目标

用于指导 agent 对比 `twitter-digest` 的两种抓取方式：

- API 抓取：`scripts/api_x_digest.py`
- 浏览器抓取：`scripts/browser_x_digest.py`

测试重点：

- 同一账号、同一时间窗口下，API 与浏览器抓到的数据差异。
- 两种方式的稳定性：是否成功、是否超时、是否出现认证/限流/页面加载失败。
- 两种方式的数据完整性：home timeline、mentions、own profile、DM/X Chat 的数量和缺口。
- 保留每轮历史原始数据，方便后续总报告和回归分析。

## 一轮测试的定义

一轮 = API 完整抓取一次 + 浏览器完整抓取一次。

每轮会分别保存：

```text
round-XX/
  api/
    digest-input.json
    digest-input.md
    digest-context.json
    digest-context.md
    stdout.log
    stderr.log
  browser/
    digest-input.json
    digest-input.md
    digest-context.json
    digest-context.md
    stdout.log
    stderr.log
  round-summary.json
  round-summary.md
```

多轮之间必须至少间隔 120 秒，避免连续请求触发 X API rate limit。测试脚本会把低于 120 的 `--interval-sec` 自动提升到 120。

## 前置条件

API 路径：

- 已通过 `python3 twitter-digest/scripts/run_daily_digest.py --configure-api` 完成 OAuth2 user-context 授权，或环境里有 `X_BEARER_TOKEN` / `TWITTER_BEARER_TOKEN`。
- token 必须是用户上下文 token。App-only token 不能可靠读取 home timeline 或用户数据。

浏览器路径：

- 已在 `twitter-digest/.state/chrome-profile` 对应的专用浏览器 profile 登录 X。
- 如果首次运行或登录态过期，浏览器抓取会打开可见窗口让用户登录。
- 如果 X Chat 要求 passcode，普通交互测试允许弹出可见窗口让用户处理；无人值守测试应加 `--non-interactive`，让脚本记录缺口后继续。

## 推荐命令

快速冒烟，只跑一轮：

```bash
python3 twitter-digest/scripts/compare_collectors.py --rounds 1
```

标准对比，跑三轮，每轮间隔至少两分钟：

```bash
python3 twitter-digest/scripts/compare_collectors.py --rounds 3 --interval-sec 120
```

可见浏览器调试：

```bash
python3 twitter-digest/scripts/compare_collectors.py --rounds 1 --headed
```

无人值守稳定性测试：

```bash
python3 twitter-digest/scripts/compare_collectors.py --rounds 3 --interval-sec 120 --non-interactive
```

指定账号 handle：

```bash
python3 twitter-digest/scripts/compare_collectors.py --rounds 3 --handle 819074233qqco
```

## 输出目录

默认输出：

```text
twitter-digest/.state/compare-runs/<YYYYMMDD-HHMMSS>/
```

总报告：

```text
comparison-report.md
comparison-report.json
```

每轮报告：

```text
round-XX/round-summary.md
round-XX/round-summary.json
```

`.state/` 已被 `.gitignore` 忽略，不会提交到仓库。报告中可能含有私信摘要或原始抓取片段，只能用于本机测试和内部排查。

## 对比维度

公开数据页：

- `home`
- `own_profile`
- `mentions_search`
- `mentions_notifications`

每页对比：

- API item 数量
- 浏览器 item 数量
- 两边重合数量
- API only 数量
- browser only 数量

DM/X Chat：

- API DM 目前只作为 TODO/调试路径。
- 浏览器 DM 是现阶段权威来源，尤其是 X Chat / 加密私信。
- 如果 API `/2/dm_events` 返回 0 条，不代表没有私信。
- 如果浏览器 DM 被 passcode、登录态、页面加载挡住，应记录为数据缺口，而不是总结成“无私信”。

## 稳定性判定

每轮记录：

- collector 是否成功退出。
- 执行耗时。
- `stdout.log` / `stderr.log`。
- endpoint 或页面级 data gap。
- 认证、权限、tier、限流、passcode、页面加载等错误摘要。

建议判定：

- 3/3 成功：当前环境稳定。
- 2/3 成功：可用但存在偶发失败，需要查看失败轮日志。
- 0-1/3 成功：不稳定，不能作为默认路径，需要优先修复认证、限流、页面加载或 passcode 流程。

## 完整性判定

公开数据：

- API 的结构化 timeline / mentions 数量通常应更稳定。
- 浏览器数量受页面加载、滚动、账号界面实验影响。
- 数量差异不一定是 bug，需要结合 `digest-input.json` 看具体 item。
- 如果某页为 0，但 `collection_error` 为空，要重点排查是否被误判为空页。

DM：

- 浏览器抓取应能看到 X Chat 列表，并至少准确统计今日可见会话、最后由我回复的会话、等待我回复的会话。
- 等待我回复的会话需要打开并尽量完整滚动加载。
- API DM 结果只用于记录当前 X API 覆盖情况，不参与最终日报判断。

## Agent 执行流程

1. 运行 `python3 twitter-digest/scripts/compare_collectors.py --rounds 3 --interval-sec 120`。
2. 等脚本自然结束。不要在两轮之间手动重跑，避免破坏间隔规则。
3. 打开输出目录下的 `comparison-report.md`。
4. 如果某轮失败，查看对应 `round-XX/<source>/stderr.log` 和 `digest-context.md`。
5. 汇总时先说明稳定性，再说明完整性差异。
6. 对 DM 结论必须明确：浏览器为准，API DM 为 TODO/调试。

## 最终报告模板

```markdown
## X 抓取对比测试报告

测试时间：
账号：
轮次：
间隔：

### 稳定性
- API：成功 N/M，主要错误：
- 浏览器：成功 N/M，主要错误：

### 数据完整性
- Home timeline：
- Mentions：
- Own profile：
- DM/X Chat：

### 关键差异
1.
2.
3.

### 结论
- 默认日报路径建议：
- 需要修复/观察的问题：
- 下次回归测试建议：
```
