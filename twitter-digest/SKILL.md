---
name: twitter-digest
description: Use when the user wants Claude Code or another agent to analyze their own X/Twitter mentions, home timeline, visible direct messages, reply opportunities, and daily social-media summaries through a local logged-in browser session.
---

# X/Twitter Digest

## Overview

Use this skill to produce a concise Chinese daily digest from the user's own X/Twitter account. The only supported access path is local browser collection with a persistent dedicated Chromium profile.

Load `references/x-twitter-digest.md` when you need implementation details, browser workflow rules, memory behavior, or the scoring rubric.

## Browser-Only Access

This skill intentionally uses only local browser automation.

Default collection uses:

```bash
python3 twitter-digest/scripts/browser_x_digest.py
```

For chat usage, run the wrapper:

```bash
python3 twitter-digest/scripts/run_daily_digest.py
```

The first run opens a dedicated browser profile at `twitter-digest/.state/chrome-profile`. The user logs in to X once in that browser. Later runs default to headless collection and reuse the saved local browser session. If the saved login is unavailable, the script automatically opens a visible browser window for manual login.

DM reading is enabled by default and only reads visible local browser content. To skip DMs for a run:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --no-dms
```

Default scope:

- Mentions of the authenticated handle.
- Home timeline hotspots.
- Own profile activity.
- Unread or newly changed visible DM conversations.
- Optional keyword searches only when the user explicitly passes `--keywords`.

Read `twitter-digest/.state/run/digest-input.md`, `twitter-digest/.state/run/digest-context.md`, and JSON if needed before writing the Chinese digest.

## Install

From the repository `skills/` directory:

```bash
python3 twitter-digest/scripts/install.py
```

Default install copies the skill to `~/.claude/skills/twitter-digest`. Local development can use `--symlink`.

The installer moves old `twitter-briefing`, `twitter-briefing.bak`, or existing `twitter-digest` installs into `~/.claude/skills/.backups/` and disables their `SKILL.md` files so Claude Code does not load duplicate old skills. It does not copy `.state` from the development checkout.

Claude Code or other agents can use the installed skill by running the same browser scripts.

## Memory

`scripts/run_daily_digest.py` updates local memory by default:

- `twitter-digest/.state/config.json`: account defaults and preferences.
- `twitter-digest/.state/memory.json`: account metadata, seen public post URLs, DM thread status signatures, and run history.
- `twitter-digest/.state/daily/YYYY-MM-DD.json`: sanitized daily archive.
- `twitter-digest/.state/daily/YYYY-MM-DD.md`: sanitized daily archive.
- `twitter-digest/.state/run/digest-input.md`: current run browser capture, annotated with `[new]` / `[repeat]` for public posts.
- `twitter-digest/.state/run/digest-context.md`: current run memory context for the final digest.

Long-term memory must not store raw DM text. Raw DM text may exist only in the current run's private `twitter-digest/.state/run/digest-input.*` files for immediate summarization. The run directory is created with owner-only permissions where supported.

Memory retention defaults:

- Seen public posts and DM thread signatures: 60 days.
- Sanitized daily archives: 90 days.
- Run dates use the user's local timezone, not UTC.

## Workflow

### 1. Collect

When the user asks for an X daily digest or X 日报, run:

```bash
python3 twitter-digest/scripts/run_daily_digest.py
```

If they ask to skip DMs:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --no-dms
```

If the authenticated handle is not detected or the user corrects it:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --handle <handle> --account-name "<显示名>" --save-default
```

For debugging or manual inspection:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --headed
```

For unattended scheduled runs that should not block on passcode recovery:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --non-interactive
```

Do not ask the user to copy cookies or configure another service. If the script opens a visible browser window, tell the user to log in or resolve the visible X challenge there.

### 2. Protect Privacy

Treat browser sessions, cookies observed internally by the script, DMs, phone numbers, emails, private handles, and screenshots as sensitive. Do not post, reply, like, follow, block, open suspicious links, accept DM requests, or send DMs unless the user explicitly asks after reviewing a draft.

Browser DM collection only reads message content visible in the logged-in local browser. If X Chat shows a passcode setup, passcode entry, or end-to-end-encryption recovery screen during headless collection, the script should automatically reopen X Messages in a visible browser window, wait for the user to complete it, then retry DM collection. In `--non-interactive` mode, record the DM data gap and continue without blocking. Do not choose, enter, or store a passcode for the user.

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

Always report DM counts when available: visible conversations, unread/new conversations, and read/history conversations. Only summarize DM bodies from `dm_status: captured_unread_threads` or from threads marked `memory_status: new_or_changed`. If the messages page shows only already-read/history threads, report `no_unread_threads` as “没有未读或新增私信需要处理”, not “没有私信”. If `visible_threads_unopened` appears, say the conversation list was visible but unread message bodies were not opened.

For DM sender attribution, use the thread `participant` / `会话对象` and message bubble direction. Do not treat authors inside quoted posts, repost cards, link previews, or embedded tweet text as the DM sender. If a DM contains a shared post by `Marco` inside a conversation with `@jerry`, the DM is from the conversation participant, not from `Marco`.

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
- 统计：可见会话 N 个，未读/新增 N 个，已读历史 N 个
- 仅总结未读或新增/变更的可见私信
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
