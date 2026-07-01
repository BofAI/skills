# X/Twitter Digest Data Collection Design

## 目标

抓数据层要稳定、可替换、可诊断。

核心约束：

- 抓取脚本只负责生成标准化的 `digest-input.*`。
- 上层摘要逻辑只读取 `digest-context.md`。
- 不同数据源必须产出相同的页面结构，方便后续处理复用。
- 用户操作从对话里触发。Agent 负责运行配置、授权、抓取和总结脚本；用户只在弹出的系统输入框或浏览器授权页里输入/确认。
- 首次配置成功后，凭据保存在本地 `.state/api_config.json`；后续生成日报不再要求用户重复输入或授权，除非 token 被撤销、过期且无法刷新，或用户主动清除配置。

## 三层脚本

### 1. 浏览器抓取脚本

```text
scripts/browser_x_digest.py
```

职责：

- 使用本地专用 Chromium profile 登录 X。
- 读取 `home`、`own_profile`、`mentions_search`、`mentions_notifications`。
- 读取 X Chat 左侧会话列表。
- 只打开 `waiting_reply` DM 会话，并尽量完整加载这些会话。
- 输出 `digest-input.json` 和 `digest-input.md`。

适合：

- 无 API 配置的普通用户。
- 需要读取 X Chat / DM 内容的场景。
- 普通日报的默认来源；即使本地已有 API 配置，未显式选择 API 时也继续使用浏览器。

### 2. API 抓取脚本

```text
scripts/api_x_digest.py
```

职责：

- 使用已保存的 OAuth2 user-context token，或 `X_BEARER_TOKEN` / `TWITTER_BEARER_TOKEN` / `--bearer-token` 传入的 OAuth2 user token。
- 主路径是 OAuth2 PKCE：用户准备 X App 的 `Client ID`，使用 `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api` 让脚本打开授权页并通过本地 callback 换取 user access token / refresh token。
- 如果用户已经有 OAuth2 user access token，使用 `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api-token` 由脚本安全保存。
- OAuth1 不再作为日报 API 配置路径，因为它不能可靠读取 DM；需要完整 DM 时走 OAuth2，API DM 拿不到时走浏览器脚本。
- 读取 home timeline：`/2/users/:id/timelines/reverse_chronological`。
- 读取用户公开发帖。
- 读取 mentions。
- 读取 recent search 中的 @ 提及。
- 读取显式配置的 keyword search。
- 输出和浏览器脚本同形状的 `digest-input.json` 和 `digest-input.md`。

适合：

- 用户显式选择 API，且需要更稳定公开数据的场景。
- 定时任务中减少浏览器页面变化影响。

限制：

- `run_daily_digest.py` 的正常日报路径不使用 API DM 做最终判断；DM / X Chat 一律由浏览器脚本读取。
- `api_x_digest.py --include-dms` 保留为 TODO/调试路径：它会尝试 `/2/dm_events`，但结果只作为 API 可见事件参考。
- Home timeline endpoint 需要可访问该用户上下文的 token；如果账号权限、套餐或 token 类型不支持，会在 `home` 页面写入具体 `collection_error`。
- App-only API key / app-only bearer token 不等于用户授权，不能保证读取用户 home timeline 或 DM。
- DM API 需要 X App / token 有 `dm.read` 相关权限；权限不足、tier 不支持、rate limit、返回 0 条或无法确认是否需要回复时，会写入 `api_dm_todo` 和 data gap。
- API DM 不等同于网页 X Chat。XChat / 加密私信可能不会出现在 `/2/dm_events`。现阶段 API DM 标记为 TODO，等待 X 修复或明确文档；日报 DM 以浏览器脚本为准。
- API 权限不足、额度不足或 endpoint 不可用时，会把错误写入对应页面的 `collection_error`。

### 3. 上层入口脚本

```text
scripts/run_daily_digest.py
```

职责：

- 统一入口。
- 提供 `--configure-api`，由 Agent 在对话里触发 OAuth 配置。
- 默认使用浏览器抓取。
- 只有用户主动要求配置/使用 X API，或命令显式传入 `--source api` / `--source auto`，才走 API 抓取。
- API source 已显式选择时不启动浏览器，不自动回退浏览器；API 不可用时失败或写入 data gap。
- 普通 `run_daily_digest.py` 即使检测到环境变量 token 或 `.state/api_config.json`，也继续使用浏览器。
- 如果 OAuth2 access token 快过期且保存了 refresh token，自动刷新后再抓取。
- 抓取完成后调用 `digest_context.py` 生成 `digest-context.*`。

选择逻辑：

```text
--source api      -> 强制 API，只采公开数据，不启动浏览器
--source browser  -> 强制浏览器，采公开网页和可见 X Chat / DM
--source auto     -> 显式选择自动模式；有 X_BEARER_TOKEN/TWITTER_BEARER_TOKEN 或已保存 OAuth2 user token 用 API，否则浏览器；API 已配置时不回退浏览器
```

隔离规则：

- API 来源只运行 `api_x_digest.py`，不启动浏览器、不读取浏览器 profile、不用浏览器补采 API 缺口。
- 浏览器来源只运行 `browser_x_digest.py`，不读取 API token、不合并 API collector 输出。
- 默认浏览器来源和 `--source auto` 每次都只选择一个来源，不合并 API 和浏览器两边的数据。
- API 输出里的“需要浏览器确认 DM”只能作为 data gap 提示，不表示本次已经读取了浏览器 DM。

## 对话触发流程

底层只保留两个抓取脚本：

```text
scripts/api_x_digest.py      -> 官方 API 抓取：home timeline、mentions、profile；API DM 仅作为 TODO/调试
scripts/browser_x_digest.py  -> 浏览器抓取：公开网页 + X Chat / 加密 DM
```

普通日报：

```text
用户：生成 X 日报
Agent：运行 scripts/run_daily_digest.py
脚本：自动选择 API 或浏览器，生成 digest-context.md
Agent：读取 digest-context.md 写中文日报
```

配置 API，已有 token：

```text
用户：输入 X token / 我已经有 token
Agent：运行 `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api-token`
脚本：弹出隐藏输入框
用户：粘贴 user access token
脚本：保存 token 到 .state/api_config.json
后续普通日报仍运行 `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py` 并默认走浏览器；要用 API 时显式运行 `--source api` 或 `--source auto`
```

配置 API，OAuth2 授权：

```text
用户：配置 X API
Agent：运行 `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api`
脚本：直接进入 OAuth2 配置
用户：输入 Client ID 和可选 Client Secret
脚本：打开 X 授权页
用户：在浏览器里授权 app
脚本：通过本地 callback 换取 access token / refresh token 并保存
后续普通日报仍运行 `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py` 并默认走浏览器；要用 API 时显式运行 `--source api` 或 `--source auto`
```

后续运行：

```text
用户：生成 X 日报
Agent：运行 scripts/run_daily_digest.py
脚本：默认使用浏览器采集并生成 digest-context.md
脚本：只有显式 `--source api` / `--source auto` 时才读取 `.state/api_config.json` 使用 API
Agent：读取 digest-context.md 写中文日报
```

如果凭据失效：

```text
脚本：如果显式使用 API，则把 API endpoint 错误写入 data gap
Agent：告知用户需要重新配置/授权
用户：在对话里说“重新配置 X API”
Agent：再次运行 `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api`
```

清除 API：

```text
用户：清除 X API 配置
Agent：运行 `python3 ~/.claude/skills/twitter-digest/scripts/configure_api.py --clear`
后续：`python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py` 默认使用浏览器抓取
```

## 标准输出结构

两种抓取方式都输出：

```text
digest-input.json
digest-input.md
```

核心 JSON 结构：

```json
{
  "generated_at": "...",
  "source": "browser|api",
  "handle": "...",
  "keywords": [],
  "pages": [
    {
      "kind": "home|own_profile|mentions_search|mentions_notifications|messages",
      "url": "...",
      "items": []
    }
  ]
}
```

公开 item 尽量包含：

- `text`
- `url`
- `time`
- `authorUrl`
- `externalLinks`
- `media`
- `cards`

DM page 尽量包含：

- `dm_status`
- `dm_note`
- `dm_visible_thread_count`
- `dm_replied_thread_count`
- `dm_unreplied_thread_count`
- `dm_captured_message_count`
- `dm_threads`

API DM TODO / 调试规则：

- 正常日报不使用 API DM 做最终判断；`run_daily_digest.py` 会用浏览器补 DM。
- 只有直接运行 `api_x_digest.py --include-dms` 做调试时，才调用 `/2/dm_events`。
- 按 `dm_conversation_id` 分组。
- 只把最后一条不是用户发出的会话正文放进 `dm_threads`，用于判断是否需要回复。
- 最后一条是用户发出的会话只计数，不展开正文。
- 如果 `/2/dm_events` 返回权限、tier、认证或限流错误，写入 `api_dm_todo` data gap，不把失败当作“无私信”。
- API 来源不启动浏览器，也不补采浏览器 DM；如果需要完整 DM，必须显式使用 `--source browser`。

## 稳定性策略

### 浏览器抓取

- 使用专用 profile，不读用户常用浏览器。
- 通过 `auth_token` cookie 判断登录态。
- 页面结构变动时，失败会进入 data gap，而不是生成伪结论。
- DM 会话只打开 `waiting_reply`。
- 需要回复的 DM 会话尽量滚到顶部。
- 未完整加载时记录 `dm_thread_incomplete`。

### API 抓取

- 使用标准 HTTP API。
- 每个页面独立采集，某个 endpoint 失败不会阻塞其他页面。
- API 错误写入页面级 `collection_error`。
- Home timeline 会先尝试官方 timeline endpoint，只有 endpoint 返回权限/额度/可用性错误时才进入 data gap。
- 没有 API token 时不报错；上层仅在完全没有 API 配置时使用浏览器。

### 上层摘要

- 不直接读取原始页面。
- 只读取 `digest-context.md`。
- `digest-context.md` 包含 data gaps。
- 模型必须把 data gaps 明确写进日报。

## 常用命令

自动选择：

```bash
python3 twitter-digest/scripts/run_daily_digest.py
```

强制浏览器：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --source browser
```

强制 API：

```bash
X_BEARER_TOKEN=... python3 twitter-digest/scripts/run_daily_digest.py --source api --handle <handle>
```

只跑浏览器抓取：

```bash
python3 twitter-digest/scripts/browser_x_digest.py --include-dms
```

只跑 API 抓取：

```bash
X_BEARER_TOKEN=... python3 twitter-digest/scripts/api_x_digest.py --handle <handle>
```
