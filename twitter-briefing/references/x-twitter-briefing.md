# X/Twitter Browser Briefing Reference

Use this reference when implementing, auditing, or troubleshooting the browser-only X/Twitter briefing workflow.

## Access Model

The only supported data access path is direct local browser automation:

- `scripts/browser_x_briefing.py` launches a dedicated Chromium profile at `~/.twitter-briefing/chrome-profile`.
- The user logs in to X once in that browser.
- Later runs default to headless collection and reuse the saved browser session.
- If the saved login is unavailable, the script automatically opens a visible browser window for manual login.
- The script reads only visible content from X pages.
- No other data access path is part of this skill.

Typical chat run:

```bash
python3 twitter-briefing/scripts/run_daily_brief.py
```

Visible DM collection is enabled by default. To skip DMs:

```bash
python3 twitter-briefing/scripts/run_daily_brief.py --no-dms
```

Optional keyword search is off by default. Use it only when the user explicitly asks:

```bash
python3 twitter-briefing/scripts/run_daily_brief.py --keywords "query one,query two"
```

Force a visible browser window for debugging:

```bash
python3 twitter-briefing/scripts/run_daily_brief.py --headed
```

Outputs:

- `/tmp/x-briefing/briefing-input.json`
- `/tmp/x-briefing/briefing-input.md`
- `/tmp/x-briefing/memory-context.json`
- `/tmp/x-briefing/memory-context.md`

## Browser Collection Rules

- Use the dedicated profile, not the user's normal browser profile.
- Do not ask the user to copy cookies or tokens.
- If X shows a login page, wait for the user to log in manually.
- If X shows CAPTCHA or account challenge, stop and ask the user to resolve it in the browser.
- Do not post, like, follow, accept DM requests, open suspicious links, or reply.
- Keep scrolling bounded. Increase `--scrolls` only when the user needs broader coverage.
- Read only DM content that is visible in the local logged-in browser. Use `--no-dms` when the user does not want DMs processed.
- If X Chat shows passcode setup, report `blocked_by_x_chat_passcode`; the user must complete that setup in the browser once.

## Pages Collected

Default browser pages:

- `home`: home timeline for hotspot detection.
- `own_profile`: the authenticated account profile.
- `mentions_search`: live search for `@handle`.
- `mentions_notifications`: notifications mentions page.
- `messages`: X Messages.

Optional pages:

- `keyword_N`: explicit search queries, only when `--keywords` is provided.

## Memory

Memory files:

- `~/.twitter-briefing/config.json`: account defaults and preferences.
- `~/.twitter-briefing/memory.json`: seen public post URLs, DM thread status signatures, account metadata, and run history.
- `~/.twitter-briefing/daily/YYYY-MM-DD.json`: sanitized daily archive.
- `~/.twitter-briefing/daily/YYYY-MM-DD.md`: sanitized markdown archive.

Privacy rule: do not persist raw DM text in memory or daily archives. Raw DM text may exist only in the current run's `/tmp/x-briefing/briefing-input.*` files for immediate summarization. Use `memory-context.md` to distinguish new, repeated, and unchanged items in the final Chinese brief.

## Hotspot Detection

Cluster home timeline posts by repeated topics, hashtags, URLs, named entities, accounts, and semantic similarity. Optional keyword-search posts may be included only when the user explicitly passes `--keywords`.

A hotspot needs at least one of:

- Multiple independent posts in the briefing window.
- One high-signal post with unusually strong engagement.
- A topic that directly affects the user's projects, brand, customers, portfolio, or community.

For each hotspot, include:

- Topic name.
- Why it is surfacing now.
- Evidence from representative posts when available.
- User relevance.
- Suggested action: monitor, reply, quote, DM, ignore, or investigate.

## Importance Scoring

Score each item from 0 to 100. Use the score to rank, not as false precision.

Suggested weights:

- Direct action requested: +25
- Time sensitivity or deadline: +20
- Reputation, security, legal, finance, or customer risk: +20
- High-relevance relationship or business opportunity: +15
- High-signal author or engagement: +10
- Repeated topic across independent sources: +10
- Spam, vague tag, automated promo, or low-context mention: -20
- Harassment, phishing, or obvious scam: classify separately as risk/ignore.

Classification bands:

- 80-100: urgent
- 60-79: important
- 35-59: routine
- 0-34: ignore/noise

## DM Handling

DMs are private. Summarize only what the user needs to decide the next action.

Red flags:

- Credential requests, wallet/private-key requests, suspicious links, payment pressure, impersonation.
- Legal threats, press inquiries, customer escalations, partner deadlines.
- People asking for personal data about someone else.

Reply drafting rules:

- Draft replies separately from the summary.
- Keep tone aligned with the user's recent posts if available.
- Do not promise commitments, prices, dates, investments, legal positions, or confidential details unless the user supplied them.
- Ask for approval before sending any reply.

## 中文每日 Prompt

```text
使用 $twitter-briefing 通过本地浏览器读取我最近 24 小时的 X/Twitter 动态，生成中文日报。重点总结谁 @ 了我、时间线热点、需要处理的私信或互动、我的账号动态。先给今日总结和行动建议，再给明细。回复只生成草稿，不要自动发送。读不到的数据要明确标注。
```
