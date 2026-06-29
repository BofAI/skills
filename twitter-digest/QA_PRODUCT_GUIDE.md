# X 日报 Skill QA / 产品操作文档

本文用于 QA、产品或非研发同事验证 `twitter-digest`。按步骤操作即可，不需要理解内部代码。

## 使用范围与限制

- 本文是独立操作文档，不依赖 README。
- 日报默认入口是 `scripts/run_daily_digest.py`。
- API 用于公开数据：home timeline、mentions、profile。
- DM / X Chat 以浏览器抓取为准；API DM 现阶段不作为可靠来源，也不参与批量对比测试。
- 浏览器抓取只读取本地已登录浏览器页面能加载出来的内容，不代表完整 X 历史。
- Skill 只读取和总结，不会自动发推、点赞、关注、回复、打开可疑链接或发送 DM。
- 批量对比测试会把每轮历史数据保存在 `.state/compare-runs/`，这些文件可能包含账号内容，应按敏感数据处理。

## 一、安装 -> 配置 -> 运行

### 1. 准备条件

环境和 X App 已配置好。测试前只需要私信找 ZC 要两项：

- OAuth2 Client ID
- OAuth2 Client Secret

拿到后按下面步骤操作即可。当前日报里 DM 以浏览器抓取为准；API 主要用于公开数据，比如 home、mentions、profile。

### 2. 安装 Skill

测试当前 PR 分支时，在 Claude Code 或 Terminal 里运行：

```bash
git clone -b twitter-digest-api-collector git@github.com:BofAI/skills.git bofai-skills
cd bofai-skills
python3 twitter-digest/scripts/install.py
```

安装成功后应看到：

```text
Codex 里运行安装：~/.codex/skills/twitter-digest
Claude Code 里运行安装：~/.claude/skills/twitter-digest
```

安装脚本会按当前工具自动选择安装目录；需要指定时可加 `--client codex` 或 `--client claude`。

安装完成后，配置和运行都以已安装目录为准：

```text
Codex: ~/.codex/skills/twitter-digest
Claude Code: ~/.claude/skills/twitter-digest
```

如果 Agent 误从临时 clone/source 目录运行配置脚本，脚本会自动切回已安装目录，避免把 `.state/api_config.json` 写到 `/tmp` 或临时项目里。

如果安装脚本提示缺浏览器，先安装 Chrome / Chromium / Edge / Brave 后重试。

### 3. 配置 X API

在 Claude Code 里说：

```text
配置 X API
```

Agent 应运行：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --configure-api
```

期望流程：

1. 自动打开一个 Terminal 配置窗口；不要在后台 shell 里直接跑交互输入。
2. 不出现 OAuth1 / 多种方式选择，直接进入 OAuth2。
3. 输入 ZC 提供的 OAuth2 Client ID。
4. 输入 ZC 提供的 OAuth2 Client Secret。
5. 浏览器打开 X 授权页。
6. 用户在浏览器里授权当前 X 账号。
7. 配置保存到：

```text
~/.claude/skills/twitter-digest/.state/api_config.json
```

8. Terminal 配置窗口结束后应自动关闭。

如果已经有 OAuth2 user access token，可单独说：

```text
输入 X token
```

这不是 QA 主流程，只用于研发调试。QA/产品测试默认只使用 ZC 提供的 OAuth2 Client ID / Client Secret。

配置后如果需要检查状态，在 Claude Code 里说：

```text
检查 X API 配置
```

Agent 应运行：

```bash
python3 twitter-digest/scripts/configure_api.py --verify
```

不要让 Agent 现场拼 `python3 -c` 或临时脚本来验证 token；内置验证命令会调用 `/users/me`，自动补全 handle / user_id，并且不会打印 token。

### 4. 首次运行日报

在 Claude Code 里说：

```text
生成今日 X 日报
```

Agent 应运行：

```bash
python3 twitter-digest/scripts/run_daily_digest.py
```

期望行为：

- 如果 API 已配置，公开数据优先走 API。
- DM / X Chat 走浏览器。
- 如果浏览器 profile 没登录，会打开浏览器让用户登录 X。
- 用户只需要在打开的浏览器里登录 X。
- 登录后，后续运行默认复用登录态并尽量 headless。

### 5. 正常输出

QA/产品只需要看 Claude Code 对话框里最终输出的中文 X 日报，不需要打开或检查脚本生成的 `json/md` 文件。

产品验收日报时重点看：

- 是否识别正确账号。
- 是否总结谁 @ 了我。
- 是否总结首页热点。
- 是否总结自己的账号动态。
- 是否统计 DM 今日可见会话、最后我发出、等我回复、捕获消息数。
- 是否明确写出数据缺口。
- 是否没有自动发推、点赞、关注、回复或打开可疑链接。

以下内容只用于研发排查，不是 QA 必须操作：

- 脚本会在本地生成 `twitter-digest/.state/run/digest-context.*` 和 `digest-input.*`。
- Agent 正常生成日报时应只读 `twitter-digest/.state/run/digest-context.md`。
- 如果 Agent 需要检查本次采集计数或 JSON 状态，应运行固定命令：

```bash
python3 twitter-digest/scripts/inspect_digest.py
```

不要允许 Agent 现场拼 `python3 -c` 或临时脚本来遍历 JSON。固定检查脚本只输出计数、状态和数据缺口，不输出 DM 正文。

### 6. 清除或重配（可选操作，非必须）

这一节只在账号配错、token 失效、需要换 X 账号、或需要重新登录浏览器时使用。正常安装、配置、运行不需要执行。

清除 API 配置：

```bash
python3 twitter-digest/scripts/configure_api.py --clear
```

重新配置：

```text
配置 X API
```

如果想重新登录浏览器账号，可以删除专用 profile 后重新跑日报：

```bash
rm -rf twitter-digest/.state/chrome-profile
python3 twitter-digest/scripts/run_daily_digest.py --source browser --headed
```

## 二、批量对比测试

### 1. 测试目标

用于比较 API 和浏览器两种抓取方式：

- 稳定性：是否能连续成功。
- 完整性：home、mentions、profile、DM 的数量和缺口。
- 差异：API 与浏览器抓到的数据是否一致、哪里不一致。

注意：

- API 对比测试只测公开数据，不测 API DM。
- DM 以浏览器结果为准。
- 一轮 = API 公开数据抓取一次 + 浏览器完整抓取一次。
- 每轮之间至少间隔 120 秒，避免 API 限流。

### 2. 快速冒烟测试

只跑 1 轮：

```bash
python3 twitter-digest/scripts/compare_collectors.py --rounds 1 --interval-sec 120
```

适合验证环境是否能跑通。

### 3. 标准对比测试

跑 3 轮：

```bash
python3 twitter-digest/scripts/compare_collectors.py --rounds 3 --interval-sec 120
```

适合普通 QA 验证。

### 4. 长稳测试

跑 20 轮：

```bash
python3 twitter-digest/scripts/compare_collectors.py --rounds 20 --interval-sec 120
```

注意：20 轮会耗时较久。不要手动缩短间隔。

### 5. 输出位置

每次批量测试会生成一个目录：

```text
twitter-digest/.state/compare-runs/<timestamp>/
```

总报告：

```text
comparison-report.md
comparison-report.json
```

每轮明细：

```text
round-XX/round-summary.md
round-XX/api/
round-XX/browser/
```

每轮都会保存：

```text
digest-input.json
digest-input.md
digest-context.json
digest-context.md
stdout.log
stderr.log
```

### 6. QA 怎么读报告

先看总报告：

```text
comparison-report.md
```

重点字段：

- `api_success`: API 成功轮数。
- `browser_success`: 浏览器成功轮数。
- `api_home`: API 首页数据量。
- `browser_home`: 浏览器首页数据量。
- `api_mentions`: API mentions 数据量。
- `browser_mentions`: 浏览器 mentions 数据量。
- `browser_dm`: 浏览器 DM 状态。

推荐判断：

- API 和浏览器成功率都等于总轮数：稳定性通过。
- API home 数量通常应高于浏览器 home，说明 API 公开数据更完整。
- 浏览器 DM 每轮都能得到稳定状态，说明 DM 路径可用。
- 如果 `stderr.log` 非空，需要打开对应轮次排查。
- 如果某页连续为 0，要看 `digest-context.md` 是否有 data gap。

### 7. 通过标准

普通 QA 可按以下标准判断：

- 安装成功，skill 出现在当前工具对应目录：Codex 为 `~/.codex/skills/twitter-digest`，Claude Code 为 `~/.claude/skills/twitter-digest`。
- `配置 X API` 直接进入 OAuth2，无 OAuth1 干扰。
- 首次登录浏览器后，后续日报能复用登录态。
- `生成今日 X 日报` 能产出中文日报。
- 日报能明确区分公开数据和 DM 数据缺口。
- 批量对比测试中 API / 浏览器没有进程级失败。
- 批量测试报告和每轮历史数据都保存在 `.state/compare-runs/`。

### 8. 常见问题

#### 配置 Terminal 没自动关闭

不影响配置结果。先看是否生成：

```text
twitter-digest/.state/api_config.json
```

如果已生成，说明配置成功。窗口关闭体验可单独记录为 UI 问题。

#### API DM 为什么不测

当前 API DM 不作为可靠来源。X Chat / 加密私信以浏览器读取结果为准。

#### 浏览器突然弹出

通常是因为：

- 首次登录。
- 登录态过期。
- X Chat 需要 passcode。
- X 要求安全验证。

用户在弹出的浏览器里完成即可。

#### 报告里 home 数量 API 和浏览器差很多

这是正常现象。API 返回结构化数据；浏览器只读取当前页面实际加载出来的内容。

#### 是否会自动回复或发消息

不会。该 skill 只读取和总结。回复只生成草稿，不自动发送。
