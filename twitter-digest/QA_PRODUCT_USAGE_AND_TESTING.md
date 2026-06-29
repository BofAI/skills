# X/Twitter Digest QA / 产品使用说明

这份文档给 QA、PM、产品同学使用。目标是按步骤完成安装、配置、生成日报，并理解测试报告支持的默认策略。

## 结论

默认使用 `run_daily_digest.py --source auto`：

- 公开数据优先使用 API：home timeline、自己的 profile、mentions、keyword search。
- DM / X Chat 一律使用浏览器：会话数量、是否等我回复、私信正文、passcode / 加密聊天状态。
- API DM 不启用，不用于判断是否有私信。
- 如果 API 未配置、失效、权限不足或限流，公开数据自动回退浏览器。

默认采集量：

- API public：最多 300 条。
- Browser public：最多 100 条。
- Browser DM：只打开“等我回复”的会话，并尽量加载完整会话历史。

## 1. 准备条件

找 ZC 私信要两项 X Developer App 信息：

- OAuth2 Client ID
- OAuth2 Client Secret

本机需要：

- Python 3.10+
- Chrome / Chromium / Edge / Brave 任意一个
- 能登录 X 的账号

## 2. 安装

在 Claude Code 里让它执行：

```bash
git clone git@github.com:BofAI/skills.git /tmp/bofai-skills
cd /tmp/bofai-skills/skills
python3 twitter-digest/scripts/install.py --client claude
```

安装完成后应存在：

```text
~/.claude/skills/twitter-digest
```

Codex 测试时使用：

```bash
python3 twitter-digest/scripts/install.py --client codex
```

安装完成后应存在：

```text
~/.codex/skills/twitter-digest
```

## 3. 配置 X API

在对话里说：

```text
配置 X API
```

Agent 应运行：

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api
```

流程：

1. 系统弹窗要求输入 OAuth2 Client ID。
2. 如果有 Client Secret，再输入 Client Secret。
3. 浏览器打开 X 授权页。
4. 用户登录并授权 App。
5. 脚本本地接收 callback，保存 token。
6. 后续日报自动使用 API，不需要重复输入 key。

保存位置：

```text
~/.claude/skills/twitter-digest/.state/api_config.json
```

不要把 token 发到聊天里。

## 4. 首次运行日报

在对话里说：

```text
生成 X 日报
```

Agent 应运行：

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py
```

首次运行可能会打开浏览器：

- 如果需要登录 X，用户在弹出的浏览器里登录一次。
- 如果 X Chat 要求 passcode，用户在弹出的浏览器里完成 passcode。
- 后续默认复用本地 profile，能 headless 运行。

运行输出：

```text
~/.claude/skills/twitter-digest/.state/run/digest-context.md
~/.claude/skills/twitter-digest/.state/run/digest-context.json
~/.claude/skills/twitter-digest/.state/run/digest-input.md
~/.claude/skills/twitter-digest/.state/run/digest-input.json
```

Agent 写日报时只读：

```text
~/.claude/skills/twitter-digest/.state/run/digest-context.md
```

不要用 `cat/head/grep/python -c` 读取这些文件，避免 Claude Code 额外弹 Bash 权限。

## 5. 日常运行规则

推荐：

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py
```

强制浏览器公开数据调试：

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --source browser --headed
```

跳过 DM：

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --no-dms
```

清除或重配 API 是可选操作，不是日常必需。

清除 API：

```bash
python3 ~/.claude/skills/twitter-digest/scripts/configure_api.py --clear
```

重新配置：

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api
```

## 6. 批量对比测试

标准 3 轮：

```bash
python3 ~/.claude/skills/twitter-digest/scripts/compare_collectors.py --rounds 3 --interval-sec 120
```

长稳 20 轮：

```bash
python3 ~/.claude/skills/twitter-digest/scripts/compare_collectors.py --rounds 20 --interval-sec 120
```

只测浏览器无头稳定性：

```bash
python3 ~/.claude/skills/twitter-digest/scripts/compare_collectors.py --rounds 10 --interval-sec 120 --skip-api --headless --non-interactive
```

测试报告输出：

```text
~/.claude/skills/twitter-digest/.state/compare-runs/<timestamp>/comparison-report.md
~/.claude/skills/twitter-digest/.state/compare-runs/<timestamp>/comparison-report.json
```

测试规则：

- 一轮 = API public 完整抓取一次 + browser 完整抓取一次。
- 每轮间隔至少 120 秒，避免 X API 限流。
- API DM 不测试。
- DM 结论只看浏览器。
- public 数据允许 API 和浏览器数量不同，不能用数量完全一致作为验收条件。

## 7. 测试数据支持

下面是现有测试报告里的关键数据摘录。QA / 产品只需要看这些汇总数字；如果要追查单轮细节，再打开原始报告目录里的 `comparison-report.md`、`digest-context.md`、`stdout.log` 和 `stderr.log`。

### 7.1 API vs Browser 20 轮对比

报告来源：`comparison-report-20260629-190844.md`

| 指标 | 结果 |
|---|---:|
| 测试轮次 | `20` |
| API 成功率 | `19/20` |
| Browser 成功率 | `20/20` |
| API DM | `not_present`，不参与判断 |
| Browser DM | `19/20` 轮 `captured_unreplied_threads`，`1/20` 轮 `visible_threads_unopened` |

公开数据平均完整性：

| 页面 | API 平均 | Browser 平均 | API 空轮次 | Browser 空轮次 |
|---|---:|---:|---:|---:|
| home | `199.6` | `11.1` | `1` | `1` |
| own_profile | `0.0` | `5.8` | `20` | `0` |
| mentions_search | `5.5` | `0.0` | `1` | `20` |
| mentions_notifications | `5.2` | `6.0` | `2` | `0` |

这组数据说明：API public 能稳定提供结构化公开数据，home 数量明显高于浏览器 UI；mentions 两条线 API 和浏览器覆盖面不同，因此不能用“数量完全一致”做验收。DM 仍只能看浏览器。

### 7.2 本地 API vs Browser 20 轮对比

报告来源：`twitter-digest/.state/compare-runs/20260629-120526/comparison-report.md`

| 指标 | 结果 |
|---|---:|
| 测试轮次 | `20` |
| API 成功率 | `20/20` |
| Browser 成功率 | `20/20` |
| API home | 每轮 `35-36` 条，平均 `35.9` |
| Browser home | 每轮 `6-31` 条，平均 `10.7` |
| API mentions | 每轮 `2` 条 |
| Browser mentions | 每轮 `2` 条 |
| Browser DM | 每轮 `captured_unreplied_threads` |

公开数据平均完整性：

| 页面 | API 平均 | Browser 平均 | API 空轮次 | Browser 空轮次 |
|---|---:|---:|---:|---:|
| home | `35.9` | `10.7` | `0` | `0` |
| own_profile | `0.0` | `0.0` | `20` | `20` |
| mentions_search | `1.0` | `0.0` | `0` | `20` |
| mentions_notifications | `1.0` | `2.0` | `0` | `0` |

这组数据说明：在已配置 API 的环境里，API 和浏览器都能连续稳定完成 20 轮；公开数据两边数量不同是预期现象，DM 由浏览器稳定补齐。

### 7.3 Headless Browser 10 轮稳定性

报告来源：`twitter_digest_headless_10_round_test_report.md`

| 指标 | 结果 |
|---|---:|
| 测试轮次 | `10` |
| 执行模式 | Headless / non-interactive |
| Browser 成功率 | `10/10 = 100%` |
| 浏览器错误数 | `0` |
| 数据缺口总数 | `0` |
| 最短耗时 | `80.59s` |
| 平均耗时 | `89.75s` |
| 最长耗时 | `98.28s` |

数据完整性：

| 页面/数据 | 最小值 | 平均值 | 最大值 | 空结果轮次 |
|---|---:|---:|---:|---:|
| Home timeline | `13` | `16.0` | `25` | `0` |
| Own profile | `2` | `2.0` | `2` | `0` |
| Mentions search | `0` | `0.0` | `0` | `10` |
| Mentions notifications | `0` | `0.0` | `0` | `10` |
| 今日 DM 会话 | `1` | `1.0` | `1` | `0` |
| 最后我发出 | `1` | `1.0` | `1` | `0` |
| 等我回复 | `0` | `0.0` | `0` | `10` |

这组数据说明：无头浏览器在连续 10 轮里没有登录态丢失、DevTools 超时、passcode 阻塞或页面级 data gap。DM 结果是“今日可见 1 个会话，最后一条都是我发出，无需回复”，不是“没有私信”。

### 7.4 产品使用结论

- 除 DM 外，公开数据默认优先 API。
- DM / X Chat 永远浏览器为准。
- 浏览器 public 作为 API 不可用时的 fallback 和调试工具。
- API DM 保留为 TODO / debug，不参与日报判断。

## 8. QA 验收要点

安装验收：

- `~/.claude/skills/twitter-digest` 存在。
- 没有重复旧 skill：`twitter-briefing` / `twitter-briefing.bak` 不应同时被 Claude 加载。

配置验收：

- `配置 X API` 能弹出输入或 Terminal 引导。
- OAuth 授权完成后，后续日报不再要求重复输入 key。

日报验收：

- 能生成中文日报。
- 公开数据来自 API 或 fallback 浏览器。
- DM 区显示会话数量、最后我发出、等我回复、捕获消息数量。
- 如果页面没加载、passcode 未处理、登录失效，日报必须写数据缺口，不能误报“没有私信”。

对比测试验收：

- `comparison-report.md` 能生成。
- API public 与 browser public 差异应被解释，不直接判失败。
- browser DM 是最终 DM 依据。
