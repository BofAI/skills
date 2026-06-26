---
name: twitter-briefing
description: Use when the user wants Codex, Claude, or another agent to connect to their X/Twitter account through MCP, OAuth, an existing connector, exported data, or API credentials to analyze personal mentions, timeline hotspots, important direct messages, reply opportunities, and daily social-media summaries. Also use when designing or troubleshooting a daily X/Twitter briefing workflow for an agent.
---

# X/Twitter 每日简报

## Overview

Use this skill to turn a user's own X/Twitter account data into a concise Chinese daily brief: who mentioned them, what topics are hot in their network, which DMs need attention, and what actions are worth taking.

Load `references/x-twitter-briefing.md` when you need implementation details, X API endpoints/scopes, MCP connector guidance, or the scoring rubric.

## 默认使用方式

优先使用纯浏览器方案：

1. **默认：本地浏览器持久登录态**：运行 `scripts/browser_x_briefing.py`，打开专用 Chrome profile。用户第一次登录 X 后，登录态保存在 `~/.twitter-briefing/chrome-profile`，后续复用，不再需要重新登录。
2. **补充：官方 X archive**：当需要更完整的 DM 或历史数据时，让用户下载官方 X archive，然后运行 `scripts/parse_x_archive.py`。
3. **备用：MCP / 第三方服务**：仅当浏览器方案不可用时使用。
4. **最后：官方 X API**：仅当用户明确需要生产级 OAuth、官方 DM 权限或稳定写操作时使用。

不要宣称一种无 API 方案能覆盖所有场景。浏览器采集只能读取登录页面可见内容；如果 DM 或历史数据不可见、不稳定，用官方 archive 补充。

默认采集命令：

```bash
python3 twitter-briefing/scripts/browser_x_briefing.py --keywords "crypto,TRON,x402,AI,BTC" --out /tmp/x-briefing
```

第一次运行会打开专用浏览器，用户登录 X。后续运行会复用登录态。

用户体验要求：全程通过聊天完成。用户只需要在第一次运行时，在弹出的专用浏览器窗口里手动登录 X 一次；之后不要再要求用户复制 cookie、配置 MCP、重启 Codex 或运行命令。后续用户只要在聊天里说「生成 X 日报」「看看今天谁 @ 我」「总结 X 热点」，代理就应直接运行浏览器采集脚本并生成中文简报。

如果用户明确同意本地读取页面可见 DM，加：

```bash
python3 twitter-briefing/scripts/browser_x_briefing.py --include-dms --out /tmp/x-briefing
```

使用生成的 `/tmp/x-briefing/briefing-input.json` 和 `/tmp/x-briefing/briefing-input.md` 作为总结依据。

本地 memory 默认开启：`scripts/run_daily_brief.py` 会维护 `~/.twitter-briefing/memory.json` 和 `~/.twitter-briefing/daily/YYYY-MM-DD.{json,md}`，并在输出目录写入 `/tmp/x-briefing/memory-context.md`。长期 memory 不保存 DM 原文，只保存账号、偏好、公开帖子 seen 状态、DM 会话状态/签名和每日归档的脱敏数据。

## Install

从仓库的 `skills/` 目录运行：

```bash
python3 twitter-briefing/scripts/install.py
```

默认会 copy 到 `~/.codex/skills/twitter-briefing`。本地开发需要实时联动源码时再使用 `--symlink`。

## Workflow

### 1. Establish Data Access

First determine which access path is available:

- The agent can run `browser_x_briefing.py` with a persistent local browser profile.
- The agent has a local cookie-based Twitter MCP connected to the user's logged-in browser session.
- The agent has another X/Twitter MCP connector.
- The user can provide an official X archive `.zip` or extracted archive folder.
- The user accepts a managed third-party MCP for public X data.
- The user has an X API app with OAuth access for their account.
- No account data is available yet.

If no data path exists, do not invent results. Explain the missing connector/API/export requirement and propose the minimum required permissions.

### Chat-Only Runbook

当用户在聊天里要求生成 X 日报时，直接执行：

```bash
python3 ~/.codex/skills/twitter-briefing/scripts/run_daily_brief.py
```

然后读取 `/tmp/x-briefing/briefing-input.md`、`/tmp/x-briefing/memory-context.md`，必要时读取 JSON，按中文模板生成日报。用 memory context 标注哪些内容是新增、重复出现、昨天延续、DM 是否有新会话或变化。

如果脚本提示等待登录，告诉用户只需要在弹出的专用浏览器窗口里登录 X。登录完成后脚本会继续运行，登录态会保存在 `~/.twitter-briefing/chrome-profile`。之后的聊天请求直接复用登录态。

账号识别规则：优先使用 `~/.twitter-briefing/config.json` 里用户确认过的 handle；其次只从 X 账号菜单识别当前账号。不要从时间线里出现频率最高的用户链接猜测账号，因为这会把被浏览到的热门账号误判为登录账号。若用户纠正账号，运行：

```bash
python3 ~/.codex/skills/twitter-briefing/scripts/run_daily_brief.py --handle <handle> --account-name "<显示名>" --save-default
```

后续日报直接使用这个已确认账号。

除非用户明确要求，不要让用户手动运行命令；由代理在聊天过程中运行脚本、读取输出、生成总结。

### 2. Protect Account Privacy

Treat OAuth tokens, cookies, DMs, phone numbers, emails, private handles, and screenshots as sensitive. Never ask the user to paste raw secrets into the conversation unless no safer setup path exists. Never post, reply, like, follow, block, or send DMs unless the user explicitly asks for that action after reviewing a draft.

### 3. Collect the Briefing Window

Default to the last 24 hours for daily summaries. For ad hoc questions, ask for the time window only if it is ambiguous and material to the answer. Prefer account-local timestamps and state the date range in the final summary.

Collect these data groups when available:

- Account identity: authenticated user id, username, display name.
- Mentions: posts that mention the user, quote posts, replies, reposts of the user's posts.
- Timeline hotspots: high-engagement posts from followed accounts, repeated topics, keywords, hashtags, URLs, and accounts appearing across the window.
- Direct messages: recent conversations, unread messages, sender identity, message text, timestamps, and links only when permission allows.
- User's own posts: recent posts and replies for context.

For browser collection, run:

```bash
python3 twitter-briefing/scripts/browser_x_briefing.py --keywords "crypto,TRON,x402,AI,BTC" --out /tmp/x-briefing
```

If the user's X handle is not auto-detected, rerun with `--handle <handle>`.

For an official X archive, run:

```bash
python3 twitter-briefing/scripts/parse_x_archive.py /path/to/twitter-archive.zip --days 1 --out /tmp/x-briefing
```

Use the generated `briefing-input.json` and `briefing-input.md` as the source data for this skill.

### 4. Analyze Mentions

Group mentions by reason to care:

- Direct asks: questions, requests for response, invitations, support requests.
- Influence: high-follower or high-engagement accounts.
- Risk: complaints, accusations, misinformation, scams, impersonation, security-sensitive posts.
- Opportunity: partnership, hiring, customer lead, investor/media attention, community praise.
- Noise: spam, generic tags, low-context reposts.

Always separate facts observed in data from inferred sentiment or importance.

### 5. Analyze Hotspots

Identify topics that are repeatedly discussed or unusually engaged with in the user's timeline or relevant network. Weight by recency, engagement velocity, number of independent posters, source credibility, and relevance to the user's known interests.

Do not present platform-wide trends unless the connector/API actually provides trend data or the user asks for broader research.

### 6. Analyze DMs

Classify each DM thread as:

- `urgent`: time-sensitive, business-critical, safety/security, money, reputation, or a clear deadline.
- `important`: meaningful relationship, opportunity, unresolved issue, or action needed without immediate deadline.
- `routine`: informational, friendly, low-risk, or easy acknowledgement.
- `ignore`: spam, phishing, harassment, or irrelevant bulk outreach.

For private messages, summarize minimally. Quote only the short phrase needed to justify the classification, and omit sensitive personal data unless the user specifically needs it.

Browser DM collection only reads message content that is visible in the logged-in local browser. If X Chat shows a passcode setup or end-to-end-encryption onboarding screen, report `blocked_by_x_chat_passcode` and ask the user to complete that setup in the opened browser once; do not choose or store a passcode for the user.

### 7. Produce the Daily Summary

除非用户另有要求，最终输出必须用中文，并使用这个结构：

```markdown
## 🐦 X 日报 - YYYY-MM-DD

**📌 今日总结**
用 2-4 句中文先给判断：今天最值得知道的事、是否有需要处理的风险/机会、建议用户怎么做。不要只罗列。

**✅ 该处理**
| 优先级 | 来自 | 为什么重要 | 建议动作 |
|---|---|---|---|

**◆ 谁 @ 了你**
- 🔴 值得回 / 需要处理
- 🟡 一般互动
- ⚪ 噪音折叠统计

**◆ 私信（DM）**
- 仅在用户允许并且数据可见时总结
- 🔴 重要 / 🟡 一般 / ⚪ 忽略

**◆ 圈内热点**
1. 热点：一句话解释 + 代表观点 + 和用户的关系

**◆ 你的动态**
- 近 24h 自己发帖/互动概况

**✍️ 建议回复草稿**
- 只给草稿，不自动发送。

**⚠️ 数据缺口**
- 哪些页面没读到、DM 是否不可见、是否只扫描了前 N 条。
```

保持简洁、有判断、可执行。价值在总结和行动建议，不是把页面内容全文搬运。

## Daily Automation

When the user wants this to run every day, first identify the environment:

- Codex, Claude Code, or another agent with scheduling support: schedule a chat prompt that invokes this skill and runs `browser_x_briefing.py`.
- External automation: run the browser script with the persistent profile, then call the agent/model to summarize the generated files.

Before enabling an automated DM summary, confirm the user understands private messages will be processed by the configured agent environment.
