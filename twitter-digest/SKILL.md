---
name: twitter-digest
description: Use when the user wants Claude Code or another agent to analyze their own X/Twitter mentions, home timeline, visible direct messages, reply opportunities, and daily social-media summaries through API or local logged-in browser collection.
---

# X/Twitter Digest

## Overview

Use this skill to produce a concise Chinese daily digest from the user's own X/Twitter account. Use `scripts/run_daily_digest.py`, which selects API collection when API credentials are configured and otherwise uses local browser collection with a persistent dedicated Chromium profile. Once API credentials are configured, `--source auto` must not open the browser; API failures should fail or report data gaps until the user fixes or clears the API configuration.

After installation, configuration and daily runs should use the installed skill copy, not a temporary clone/source checkout. Installed locations are `~/.claude/skills/twitter-digest` for Claude Code and `~/.codex/skills/twitter-digest` for Codex. If `run_daily_digest.py` or `configure_api.py` is accidentally run from a source checkout while an installed copy exists, the script automatically re-runs the installed copy so `.state` is written to the installed skill directory.

Use a stable installed command form for normal chat-triggered runs. This keeps Claude Code's Bash permission prompt stable and lets the user's first "don't ask again" approval apply to future runs from different projects:

- Claude Code: `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py`
- Codex: `python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py`

In command examples below, `RUN_DAILY_DIGEST` means the matching installed command above for the current agent. Do not rely on `python3 twitter-digest/scripts/run_daily_digest.py` after installation unless you are intentionally working inside a source checkout.

For API maintenance commands, `CONFIGURE_API` means the matching installed configure command:

- Claude Code: `python3 ~/.claude/skills/twitter-digest/scripts/configure_api.py`
- Codex: `python3 ~/.codex/skills/twitter-digest/scripts/configure_api.py`

For summary writing, read the installed current-run context with the agent's file Read tool, not Bash. The normal context path is:

- Claude Code: `~/.claude/skills/twitter-digest/.state/run/digest-context.md`
- Codex: `~/.codex/skills/twitter-digest/.state/run/digest-context.md`

Do not use `cat`, `head`, `tail`, `grep`, `sed`, `python3 -c`, or temporary scripts to read or inspect `digest-context.*` / `digest-input.*` during normal analysis. Those shell reads cause extra Claude Code Bash permission prompts and may expose private DM text in command output.

Load `references/x-twitter-digest.md` when you need implementation details, browser workflow rules, current-run context behavior, or the scoring rubric.

## Data Collection

There are three collection scripts:

```bash
python3 twitter-digest/scripts/browser_x_digest.py   # browser collector
python3 twitter-digest/scripts/api_x_digest.py       # API collector
python3 twitter-digest/scripts/run_daily_digest.py   # upper wrapper, --source auto
```

For chat usage, run the wrapper:

```bash
RUN_DAILY_DIGEST
```

`run_daily_digest.py --source auto` uses saved OAuth2 user-context credentials, `X_BEARER_TOKEN`, or `TWITTER_BEARER_TOKEN` for public data when present; otherwise it uses the browser collector. When API credentials are present, `auto` does not fall back to browser on API errors. Treat API DM lookup as TODO / waiting for X to fix XChat-encrypted DM coverage; do not use API DM to decide whether the user has private messages.

Source isolation is strict:

- API source runs only `api_x_digest.py`. It never starts a browser, never opens X pages, never reads the browser profile, and never supplements missing API data with browser data.
- Browser source runs only `browser_x_digest.py`. It uses the dedicated browser profile and does not use saved API tokens or API collector output.
- `--source auto` picks exactly one source for the run: API when API credentials exist, otherwise browser. It does not merge both sources.
- If API output says DM needs browser confirmation, treat that as a data gap note only. It does not mean browser data was collected.

If the user asks to configure API access, trigger the OAuth/user-token setup from chat:

```bash
RUN_DAILY_DIGEST --configure-api
```

This is an agent-triggered flow. It supports OAuth2 user authorization:

- OAuth2 path: if the user has an X Developer App OAuth2 `Client ID` / `Client Secret` and local callback URL, run `RUN_DAILY_DIGEST --configure-api`. It goes directly into OAuth2 setup. Request `dm.read tweet.read users.read offline.access`.
- Existing token path: if the user says they already have an OAuth2 user access token, run `RUN_DAILY_DIGEST --configure-api-token`.
- If the agent is not inside an interactive Terminal, do not background `configure_api.py` yourself. Use `run_daily_digest.py --configure-api`; it opens a real Terminal window for secure input and OAuth callback handling. `configure_api.py --oauth` also self-opens Terminal when invoked non-interactively, but the wrapper is the primary path.
- OAuth1 PIN is not a supported normal setup path for this skill because it did not reliably return DM data during validation. Do not guide users to Consumer Key / Consumer Secret / PIN unless they are explicitly debugging legacy API behavior.
- Do not write ad-hoc inline Python or shell snippets to verify tokens. Use the built-in verifier: `CONFIGURE_API --verify`. It calls `/users/me`, backfills `handle` / `user_id`, and does not print the token.

If a refresh token is saved, later daily runs refresh the access token automatically. Do not ask the user to export environment variables manually. App-only API keys are not enough for user-context home timeline access.

After API setup succeeds once, future daily digest runs should not ask the user for credentials again. Run `RUN_DAILY_DIGEST`; it reads `.state/api_config.json` automatically. OAuth2 credentials are refreshed automatically when a refresh token is saved. Only rerun `--configure-api` when the saved credentials are missing, revoked, expired without refresh, or the user explicitly asks to change accounts/apps.

If the user asks to clear API access, run:

```bash
CONFIGURE_API --clear
```

All normal flows should be triggered from chat by the agent:

- X 日报 / 生成日报: run `RUN_DAILY_DIGEST`.
- 用户已有 token / 输入 X token: run `RUN_DAILY_DIGEST --configure-api-token`.
- 配置 X API / 给 app 授权: run `RUN_DAILY_DIGEST --configure-api`.
- 验证 X API 配置: run `CONFIGURE_API --verify`.
- 检查本次采集计数 / JSON 结构: run `scripts/inspect_digest.py`.
- 清除 X API 配置: run `CONFIGURE_API --clear`.
- 调试浏览器: run `RUN_DAILY_DIGEST --source browser --headed`.

Force a script source:

```bash
RUN_DAILY_DIGEST --source browser
X_BEARER_TOKEN=... RUN_DAILY_DIGEST --source api --handle <handle>
```

Browser-source runs use a dedicated browser profile at `twitter-digest/.state/chrome-profile`. The user logs in to X once in that browser. Later browser runs default to headless collection and reuse the saved local browser session. If the saved login is unavailable during a browser-source run, the script automatically opens a visible browser window for manual login. API-source runs do not touch this profile. The skill has two collector scripts: `scripts/api_x_digest.py` for official API public data, and `scripts/browser_x_digest.py` for browser-visible X Chat / encrypted DM content. API-visible DM events remain TODO-only until X fixes or documents reliable XChat coverage.

DM reading is enabled by default only for browser-source runs and only reads visible local browser content. API-source runs do not start a browser, even when `--include-dms` is passed. To skip DMs for a browser run:

```bash
RUN_DAILY_DIGEST --no-dms
```

Default scope:

- Mentions of the authenticated handle.
- Home timeline hotspots.
- Own profile activity.
- Today's visible DM conversations, with only conversations whose latest preview is not from the user opened for content.
- Optional keyword searches only when the user explicitly passes `--keywords`.

Public timeline/profile/mentions pages use the same daily-window loading model as DMs. API public collection keeps up to 300 items; browser public collection scrolls each public page up to 40 rounds, keeps up to 100 public items, waits for DOM growth after each scroll, and only allows early stop after at least 5 scroll rounds when loaded post timestamps show content beyond the 24-hour digest window (`--scrolls 40`, `--min-public-scrolls 5`, `--max-public-items 100`, `--public-window-hours 24`).

Read the installed `digest-context.md` with the file Read tool when writing the Chinese digest. Its `Final Summary Facts` section is the content source for the final summary. If more focused context is needed, use the file Read tool on the split current-run files: `digest-context-timeline.md` for home/profile/timeline items, `digest-context-mentions.md` for @ mentions, and `digest-context-dm.md` for visible DM conversations. Use `digest-input.md` only when debugging collection issues, not during normal summarization. Do not add content from older runs. Do not write ad-hoc `python3 -c`, shell, `cat`, `head`, `tail`, `grep`, or temporary scripts to inspect context structure during normal summarization. If counts or non-content structure must be checked, run the built-in `scripts/inspect_digest.py`, which does not print DM bodies.

## Install

From the repository `skills/` directory:

```bash
python3 twitter-digest/scripts/install.py
```

Default install targets the current agent client: Codex installs to `~/.codex/skills/twitter-digest`, Claude Code installs to `~/.claude/skills/twitter-digest`. Use `--client codex`, `--client claude`, or `--skills-dir` to override. Local development can use `--symlink`.

For Claude Code, the skill cannot silently grant itself Bash permission or file access outside the project. On first use, approve the visible `run_daily_digest.py` command and choose "don't ask again" if appropriate. For a global opt-in during install, run:

```bash
python3 twitter-digest/scripts/install.py --client claude --allow-claude-commands --allow-claude-state-read
```

This explicitly adds one Claude Code Bash allow rule for `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py:*` and adds `~/.claude/skills/twitter-digest/.state` to Claude Code `additionalDirectories` so the Read tool can read `digest-context.md` without a separate file-access prompt. It does not bypass permissions globally and does not grant arbitrary Bash access.

The installer checks for Python 3.10+ and a supported Chromium browser before installing. Supported browsers are Google Chrome, Chromium, Microsoft Edge, and Brave. If the browser will be installed later, use `--skip-browser-check`.

The installer moves old `twitter-briefing`, `twitter-briefing.bak`, or existing `twitter-digest` installs into the selected skills directory's `.backups/` folder and disables their `SKILL.md` files so the current agent does not load duplicate old skills. It preserves `.state` from an existing installed `twitter-digest` copy during reinstall, but does not copy `.state` from the development checkout.

Claude Code or other agents can use the installed skill by running the same browser scripts.

## Run Outputs

`scripts/run_daily_digest.py` does not write long-term memory. Each run writes only current-run files:

- `twitter-digest/.state/config.json`: account defaults and preferences.
- `<installed-skill>/.state/run/digest-context.md`: the normal top-level input for AI daily-summary writing.
- `<installed-skill>/.state/run/digest-context.json`: machine-readable version of the same normalized facts.
- `<installed-skill>/.state/run/digest-context-timeline.md`: focused current-run timeline/profile context for file Read.
- `<installed-skill>/.state/run/digest-context-mentions.md`: focused current-run @ mention context for file Read.
- `<installed-skill>/.state/run/digest-context-dm.md`: focused current-run DM context for file Read.
- `<installed-skill>/.state/run/digest-input.md`: raw collector capture for debugging only.
- `<installed-skill>/.state/run/digest-input.json`: raw machine-readable collector capture for debugging only.

No `memory.json` or `daily/` archive is produced. Raw DM text or DM excerpts may exist only in the current run's private `twitter-digest/.state/run/digest-input.*` and `digest-context.*` files for immediate summarization/debugging. The run directory is created with owner-only permissions where supported. Run dates use the user's local timezone.

## Workflow

### 1. Collect

When the user asks for an X daily digest or X 日报, run:

```bash
RUN_DAILY_DIGEST
```

If they ask to skip DMs:

```bash
RUN_DAILY_DIGEST --no-dms
```

If the authenticated handle is not detected or the user corrects it:

```bash
RUN_DAILY_DIGEST --handle <handle> --account-name "<显示名>" --save-default
```

For debugging or manual inspection:

```bash
RUN_DAILY_DIGEST --headed
```

For unattended scheduled runs that should not block on passcode recovery:

```bash
RUN_DAILY_DIGEST --non-interactive
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

Always report DM conversation counts and message counts separately when available. Conversation counts come from today's X Chat list items only: today visible conversations, conversations whose latest preview is from the user (`You:` / `You sent` / `你:`), and conversations waiting for the user's reply. The browser collector first scans the DM conversation list downward up to 20 rounds (`--dm-list-scrolls 20`) so it is not limited to the first visible screen; older conversations found in the list are ignored for the daily count. Message counts come only from opened waiting-reply conversations and represent captured message bubbles. The collector now tries to load each opened waiting-reply conversation completely by scrolling upward until the browser reaches the thread top; defaults are a 200-scroll safety limit and up to 2000 kept message bubbles (`--dm-scrolls 200`, `--dm-max-messages 2000`, `--dm-window-hours 0`). If the conversation list does not finish scanning, the digest context records `dm_list_incomplete`; if a thread does not reach the top or hits the message cap, it records `dm_thread_incomplete`. Only summarize DM bodies from `dm_status: captured_unreplied_threads`. If today's visible conversations all have latest previews from the user, report `no_unreplied_threads` as “今天可见私信会话最后一条都是我发出的，无需处理”, not “没有私信”. If `no_today_threads` appears, say there were visible older conversations but no today conversations. If `visible_threads_unopened` appears, say the conversation list was visible but waiting-reply message bodies were not opened.

If X Messages shows a skeleton/loading conversation list or `Start Conversation` while the left list is still placeholder content, do not treat it as an empty inbox. The browser collector detects this state, reloads `/messages` up to 3 times, and records `dm_page_loading_timeout` if the list never becomes readable.

For waiting-reply DMs, still summarize selectively. Count all waiting-reply conversations, but only include DMs with action value, relationship value, risk, money/security implications, or clear user relevance in the digest. Obvious spam, phishing, generic promotion, low-context links, or repeated junk should be counted and classified as ignore/noise without copying the content into the main summary.

For DM sender attribution, use the thread `participant` / `会话对象` and message bubble direction. Do not treat authors inside quoted posts, repost cards, link previews, or embedded tweet text as the DM sender. If a DM contains a shared post by `Marco` inside a conversation with `@jerry`, the DM is from the conversation participant, not from `Marco`.

When `digest-context.md` includes `### DM Thread Context`, use that section to understand the recent conversation history for waiting-reply DMs. It may include up to 2000 loaded message bubbles per summarized thread, plus raw thread label, URL, and load metadata, so the model can understand complex context before deciding whether and how to mention the DM. Keep the final digest concise; do not paste the full DM history into the report.

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
