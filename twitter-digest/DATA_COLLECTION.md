# X/Twitter Digest Data Collection Design

## 目标

抓数据层要稳定、可替换、可诊断。

核心约束：

- 抓取脚本只负责生成标准化的 `digest-input.*`。
- 上层摘要逻辑只读取 `digest-context.md`。
- 不同数据源必须产出相同的页面结构，方便后续处理复用。
- 用户操作从对话里触发。Agent 负责运行配置、授权、抓取和总结脚本；用户只在弹出的系统输入框或浏览器授权页里输入/确认。

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
- API 权限不足时的 fallback。

### 2. API 抓取脚本

```text
scripts/api_x_digest.py
```

职责：

- 使用 `X_BEARER_TOKEN` / `TWITTER_BEARER_TOKEN` 或 `--bearer-token`。
- 更推荐使用 `scripts/run_daily_digest.py --configure-api` 走 OAuth 用户授权，由脚本保存 user-context access token。
- 读取 home timeline：`/2/users/:id/timelines/reverse_chronological`。
- 读取用户公开发帖。
- 读取 mentions。
- 读取 recent search 中的 @ 提及。
- 读取显式配置的 keyword search。
- 输出和浏览器脚本同形状的 `digest-input.json` 和 `digest-input.md`。

适合：

- API 已配置、需要更稳定公开数据的场景。
- 定时任务中减少浏览器页面变化影响。

限制：

- 默认不读取 X Chat / DM 正文。
- Home timeline endpoint 需要可访问该用户上下文的 token；如果账号权限、套餐或 token 类型不支持，会在 `home` 页面写入具体 `collection_error`。
- App-only API key / app-only bearer token 不等于用户授权，不能保证读取用户 home timeline。
- API 权限不足、额度不足或 endpoint 不可用时，会把错误写入对应页面的 `collection_error`。

### 3. 上层入口脚本

```text
scripts/run_daily_digest.py
```

职责：

- 统一入口。
- 提供 `--configure-api`，由 Agent 在对话里触发 OAuth 配置。
- 默认 `--source auto`。
- 如果检测到环境变量 token 或 `.state/api_config.json` 里保存的 OAuth user access token，走 API 抓取。
- 如果没有 API token，走浏览器抓取。
- 如果 OAuth access token 快过期且保存了 refresh token，自动刷新后再抓取。
- 抓取完成后调用 `digest_context.py` 生成 `digest-context.*`。

选择逻辑：

```text
--source api      -> 强制 API
--source browser  -> 强制浏览器
--source auto     -> 有 X_BEARER_TOKEN/TWITTER_BEARER_TOKEN 或已保存 OAuth token 用 API，否则浏览器
```

## 对话触发流程

普通日报：

```text
用户：生成 X 日报
Agent：运行 scripts/run_daily_digest.py
脚本：自动选择 API 或浏览器，生成 digest-context.md
Agent：读取 digest-context.md 写中文日报
```

配置 API：

```text
用户：配置 X API
Agent：运行 scripts/run_daily_digest.py --configure-api
脚本：弹出 OAuth / Paste Token 选择
用户：选择 OAuth，输入 X Developer App Client ID
脚本：打开 X 授权页，用户在浏览器里授权
脚本：本地 callback 接收授权码，换取 user-context access token 并保存
后续：run_daily_digest.py --source auto 自动走 API
```

清除 API：

```text
用户：清除 X API 配置
Agent：运行 scripts/configure_api.py --clear
后续：run_daily_digest.py --source auto 自动回到浏览器抓取
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
- 没有 API token 时不报错，由上层自动 fallback 到浏览器。

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

只测试 DM：

```bash
python3 twitter-digest/scripts/test_dm_collection.py
```
