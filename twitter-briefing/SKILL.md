---
name: twitter-briefing
description: Use when the user wants Codex, Claude, or another agent to analyze their own X/Twitter mentions, home timeline, visible direct messages, reply opportunities, and daily social-media summaries through a local logged-in browser session.
---

# X/Twitter 每日简报

## Overview

Use this skill to produce a concise Chinese daily brief from the user's own X/Twitter account. The only supported access path is local browser collection with a persistent dedicated Chromium profile.

Load `references/x-twitter-briefing.md` when you need implementation details, browser workflow rules, memory behavior, or the scoring rubric.

## Browser-Only Access

This skill intentionally uses only local browser automation.

Default collection uses:

```bash
python3 twitter-briefing/scripts/browser_x_briefing.py --out /tmp/x-briefing
```

For chat usage, run the wrapper:

```bash
python3 ~/.codex/skills/twitter-briefing/scripts/run_daily_brief.py
```

The first run opens a dedicated browser profile at `~/.twitter-briefing/chrome-profile`. The user logs in to X once in that browser. Later runs reuse the saved local browser session.

When the user explicitly approves local DM reading, include:

```bash
python3 ~/.codex/skills/twitter-briefing/scripts/run_daily_brief.py --include-dms
```

Default scope:

- Mentions of the authenticated handle.
- Home timeline hotspots.
- Own profile activity.
- Visible DM conversations only when `--include-dms` is used.
- Optional keyword searches only when the user explicitly passes `--keywords`.

Read `/tmp/x-briefing/briefing-input.md`, `/tmp/x-briefing/memory-context.md`, and JSON if needed before writing the Chinese brief.

## Install

From the repository `skills/` directory:

```bash
python3 twitter-briefing/scripts/install.py
```

Default install copies the skill to `~/.codex/skills/twitter-briefing`. Local development can use `--symlink`.

Claude Code or other agents can use the same installed skill by running the same browser scripts.

## Memory

`scripts/run_daily_brief.py` updates local memory by default:

- `~/.twitter-briefing/config.json`: account defaults and preferences.
- `~/.twitter-briefing/memory.json`: account metadata, seen public post URLs, DM thread status signatures, and run history.
- `~/.twitter-briefing/daily/YYYY-MM-DD.json`: sanitized daily archive.
- `~/.twitter-briefing/daily/YYYY-MM-DD.md`: sanitized daily archive.
- `/tmp/x-briefing/memory-context.md`: current run memory context for the final brief.

Long-term memory must not store raw DM text. Raw DM text may exist only in the current run's `/tmp/x-briefing/briefing-input.*` files for immediate summarization.

## Workflow

### 1. Collect

When the user asks for an X daily brief, run:

```bash
python3 ~/.codex/skills/twitter-briefing/scripts/run_daily_brief.py
```

If they ask to include DMs:

```bash
python3 ~/.codex/skills/twitter-briefing/scripts/run_daily_brief.py --include-dms
```

If the authenticated handle is not detected or the user corrects it:

```bash
python3 ~/.codex/skills/twitter-briefing/scripts/run_daily_brief.py --handle <handle> --account-name "<显示名>" --save-default
```

Do not ask the user to copy cookies or configure another service. If the script waits for login, tell the user to log in inside the opened dedicated browser window.

### 2. Protect Privacy

Treat browser sessions, cookies observed internally by the script, DMs, phone numbers, emails, private handles, and screenshots as sensitive. Do not post, reply, like, follow, block, open suspicious links, accept DM requests, or send DMs unless the user explicitly asks after reviewing a draft.

Browser DM collection only reads message content visible in the logged-in local browser. If X Chat shows a passcode setup or end-to-end-encryption onboarding screen, report `blocked_by_x_chat_passcode` and ask the user to complete that setup in the opened browser once; do not choose or store a passcode for the user.

### 3. Analyze

Group mentions by reason to care:

- Direct asks: questions, requests, invitations, support requests.
- Influence: high-signal accounts or high engagement.
- Risk: complaints, misinformation, scams, impersonation, security-sensitive posts.
- Opportunity: partnership, hiring, customer lead, investor/media attention, community praise.
- Noise: spam, generic tags, low-context reposts.

Classify DMs as:

- `urgent`: time-sensitive, business-critical, safety/security, money, reputation, or deadline.
- `important`: meaningful relationship, opportunity, unresolved issue, or action needed.
- `routine`: informational, friendly, low-risk, or easy acknowledgement.
- `ignore`: spam, phishing, harassment, or irrelevant bulk outreach.

For private messages, summarize minimally. Quote only the short phrase needed to justify classification, and omit sensitive personal data unless the user specifically needs it.

### 4. Produce The Daily Summary

除非用户另有要求，最终输出必须用中文，并使用这个结构：

```markdown
## 🐦 X 日报 - YYYY-MM-DD

**📌 今日总结**
用 2-4 句中文先给判断：今天最值得知道的事、是否有需要处理的风险/机会、建议用户怎么做。

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

**◆ 时间线热点**
1. 热点：一句话解释 + 代表观点 + 和用户的关系

**◆ 你的动态**
- 近 24h 自己发帖/互动概况

**✍️ 建议回复草稿**
- 只给草稿，不自动发送。

**⚠️ 数据缺口**
- 哪些页面没读到、DM 是否不可见、是否只扫描了前 N 条。
```

保持简洁、有判断、可执行。价值在总结和行动建议，不是把页面内容全文搬运。
