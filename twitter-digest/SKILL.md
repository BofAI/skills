---
name: twitter-digest
description: Use when the user wants Claude Code or another agent to analyze their own X/Twitter mentions, home timeline, visible direct messages, reply opportunities, and daily social-media summaries through the hosted X MCP plus local logged-in browser collection for X Chat/DM.
---

# X/Twitter Digest

## Overview

Use this skill to produce a concise Chinese X/Twitter digest from the user's own account. The current architecture is MCP-first:

- Public/account data comes from the hosted X MCP installed in the AI client.
- X Chat/DM content comes from the local browser collector because encrypted X Chat may not be fully exposed through API/MCP.
- No local public-data API script is used. The agent calls MCP tools directly and writes the final digest from those tool results.

Load `references/x-twitter-digest.md` only when you need implementation details, browser rules, or the scoring rubric.

## Required X MCP

The AI client should expose an MCP server named `xapi` or similar. Configure it through `xurl`, not by asking the user to paste tokens into chat:

```bash
npm install -g @xdevplatform/xurl
xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --redirect-uri http://localhost:8080/callback
xurl auth oauth2 --app my-app
xurl auth default my-app
```

For Codex:

```toml
[mcp_servers.xapi]
command = "xurl"
args = ["mcp", "https://api.x.com/mcp"]

[mcp_servers.x-docs]
url = "https://docs.x.com/mcp"
```

For a specific authorized X user:

```toml
args = ["mcp", "-u", "USERNAME", "https://api.x.com/mcp"]
```

The X Developer App must allow the exact redirect URI used by `xurl`, commonly:

```text
http://localhost:8080/callback
```

Use `Read and write and Direct message` permissions if the user wants the broad default `xurl` scopes. Client ID and Client Secret are entered in the local terminal only.

When the user asks the agent to install or configure X MCP, the agent should
open a real local terminal window for Client ID / Client Secret entry whenever
the environment supports it. Do not merely print commands and ask the user to
run them if the agent can launch Terminal.app or an equivalent visible terminal.
After the user completes terminal input and OAuth, verify with `xurl auth status`
and then write or update the AI client's `xapi` MCP config. If no visible
terminal can be opened, fall back to concise manual instructions.

## Skill Structure

- `X MCP`: primary source for home timeline, mentions, own posts, user lookup, recent search, trends/news/articles when relevant, and optional keyword searches.
- `scripts/collect_browser_dm.py`: command-line collector for visible X Chat/DM. It writes `browser-dm-context.md/json`.
- `lib/browser_dm_core.py`: internal browser/CDP implementation used by `collect_browser_dm.py`.
- `.state/run/browser-dm-context.md|json`: current-run browser DM facts. Treat these as sensitive when they include DM text.

## Collection Rules

- For X 日报 / 周报, call X MCP tools directly for public/account data.
- Run the browser collector only when DM/X Chat coverage is needed.
- Do not use cookie-based Twitter MCP servers such as `agent-twitter-client-mcp` for this skill.
- If browser collection is used, use the installed command path:
  - Codex: `python3 ~/.codex/skills/twitter-digest/scripts/collect_browser_dm.py`
  - Claude Code: `python3 ~/.claude/skills/twitter-digest/scripts/collect_browser_dm.py`
- Do not treat `xurl dms` or MCP DM returning 0 events as proof that browser X Chat is empty.
- Do not send, like, follow, accept DM requests, or open suspicious links unless the user explicitly asks after reviewing a draft.

## Install

From the repository `skills/` directory:

Codex:

```bash
python3 twitter-digest/scripts/install.py --skills-dir ~/.codex/skills
```

Claude Code:

```bash
python3 twitter-digest/scripts/install.py
```

Default install copies the skill to `~/.claude/skills/twitter-digest`. Use `--skills-dir ~/.codex/skills` for Codex. Local development can use `--symlink`.

The installer checks for Python 3.10+ and a supported Chromium browser before installing. Supported browsers are Google Chrome, Chromium, Microsoft Edge, and Brave. If the browser will be installed later, use `--skip-browser-check`.

The installer moves old `twitter-briefing`, `twitter-briefing.bak`, or existing `twitter-digest` installs into `~/.claude/skills/.backups/` and disables their `SKILL.md` files so Claude Code does not load duplicate old skills. It does not copy `.state` from the development checkout.

Claude Code or other agents can use the installed skill by running the same browser scripts.

## Run Outputs

`scripts/collect_browser_dm.py` does not write long-term memory. Each run writes only current-run browser DM files:

- `twitter-digest/.state/run/browser-dm-context.md`: readable browser DM context.
- `twitter-digest/.state/run/browser-dm-context.json`: machine-readable browser DM context.

No `memory.json`, `daily/` archive, API token cache, or public-data capture is produced by the MCP-first flow. Public data stays in the agent's MCP tool results. Raw DM text may exist only in the current run's private `.state/run/browser-dm-context.*` files for immediate summarization/debugging.

## Workflow

### 1. Collect

When the user asks for an X daily digest, weekly digest, or X 日报/周报:

1. Use X MCP for public/account data: authenticated user, home timeline, mentions, own posts, and explicit keyword/search queries.
2. Use an appropriate time window for the request: 24 hours for daily digest, 7 days for weekly digest unless the user asks otherwise.
3. If DMs are included, run browser collection for visible X Chat/DM:

Codex:

```bash
python3 ~/.codex/skills/twitter-digest/scripts/collect_browser_dm.py
```

Claude Code:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/collect_browser_dm.py
```

If the saved browser profile is not logged in, the script opens a visible browser window and waits for the user to log in. If X Chat asks for passcode setup, passcode entry, or encryption-key recovery, the script opens or reuses a visible browser window, waits for the user to complete the challenge, then retries DM collection. For debugging, add `--headed`.

### 2. Protect Privacy

Treat browser sessions, cookies observed internally by the script, DMs, phone numbers, emails, private handles, and screenshots as sensitive. Do not post, reply, like, follow, block, open suspicious links, accept DM requests, or send DMs unless the user explicitly asks after reviewing a draft.

Browser DM collection only reads message content visible in the logged-in local browser. If X Chat shows a passcode setup, passcode entry, or end-to-end-encryption recovery screen, wait for the user to complete it in the visible browser and retry collection. In `--non-interactive` mode only, record the DM data gap and continue. Do not choose, enter, or store a passcode for the user.

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

Always report DM conversation counts and message counts separately when available. Conversation counts come from today's X Chat list items only: today visible conversations, conversations whose latest preview is from the user (`You:` / `You sent` / `你:`), and conversations waiting for the user's reply. Older conversations visible in the list are ignored for the daily count. Message counts come only from opened waiting-reply conversations and represent captured message bubbles. The collector now tries to load each opened waiting-reply conversation completely by scrolling upward until the browser reaches the thread top; defaults are a 200-scroll safety limit and up to 2000 kept message bubbles (`--dm-scrolls 200`, `--dm-max-messages 2000`, `--dm-window-hours 0`). If a thread does not reach the top or hits the message cap, the digest context records a `dm_thread_incomplete` data gap. Only summarize DM bodies from `dm_status: captured_unreplied_threads`. If today's visible conversations all have latest previews from the user, report `no_unreplied_threads` as “今天可见私信会话最后一条都是我发出的，无需处理”, not “没有私信”. If `no_today_threads` appears, say there were visible older conversations but no today conversations. If `visible_threads_unopened` appears, say the conversation list was visible but waiting-reply message bodies were not opened.

For waiting-reply DMs, still summarize selectively. Count all waiting-reply conversations, but only include DMs with action value, relationship value, risk, money/security implications, or clear user relevance in the digest. Obvious spam, phishing, generic promotion, low-context links, or repeated junk should be counted and classified as ignore/noise without copying the content into the main summary.

For DM sender attribution, use the thread `participant` / `会话对象` and message bubble direction. Do not treat authors inside quoted posts, repost cards, link previews, or embedded tweet text as the DM sender. If a DM contains a shared post by `Marco` inside a conversation with `@jerry`, the DM is from the conversation participant, not from `Marco`.

When `browser-dm-context.md` includes thread messages, use that section to understand the recent conversation history for waiting-reply DMs. It may include loaded message bubbles plus raw thread label, URL, and load metadata, so the model can understand complex context before deciding whether and how to mention the DM. Keep the final digest concise; do not paste the full DM history into the report.

Use media and link metadata when present. Public items and DM message context may include `media`, `link`, and `card` lines with image/video URLs, alt text, shared-post links, and external links. Treat these as context for understanding the item, but do not open suspicious links or overstate image contents beyond the available alt/text/URL signals.

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
- 会话统计：今日可见会话 N 个，最后我发出 N 个，等我回复 N 个
- 消息统计：已打开等我回复会话中捕获消息 N 条
- 仅挑重点总结等我回复的私信；垃圾、钓鱼、低质营销只计数并归为忽略
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
