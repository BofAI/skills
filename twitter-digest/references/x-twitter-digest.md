# X/Twitter Browser Digest Reference

Use this reference when implementing, auditing, or troubleshooting the browser-only X/Twitter digest workflow.

## Access Model

The only supported data access path is direct local browser automation:

- `scripts/browser_x_digest.py` launches a dedicated Chromium profile at `twitter-digest/.state/chrome-profile`.
- The user logs in to X once in that browser.
- Later runs default to headless collection and reuse the saved browser session.
- If the saved login is unavailable, the script automatically opens a visible browser window for manual login.
- The script reads only visible content from X pages.
- No other data access path is part of this skill.

Typical chat run:

```bash
python3 twitter-digest/scripts/run_daily_digest.py
```

Visible DM collection is enabled by default. To skip DMs:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --no-dms
```

Optional keyword search is off by default. Use it only when the user explicitly asks:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --keywords "query one,query two"
```

Force a visible browser window for debugging:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --headed
```

For unattended scheduled runs that should not open a visible browser or wait on passcode recovery:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --non-interactive
```

Outputs:

- `twitter-digest/.state/run/digest-input.json`: raw browser capture.
- `twitter-digest/.state/run/digest-input.md`: readable raw browser capture.
- `twitter-digest/.state/run/digest-context.json`: memory context plus normalized facts.
- `twitter-digest/.state/run/digest-context.md`: primary final summary input. Read this first.

## Browser Collection Rules

- Use the dedicated profile, not the user's normal browser profile.
- Do not ask the user to copy cookies or tokens.
- If X shows a login page, wait for the user to log in manually.
- If X shows CAPTCHA or account challenge, stop and ask the user to resolve it in the browser.
- Do not post, like, follow, accept DM requests, open suspicious links, or reply.
- Keep scrolling bounded. Increase `--scrolls` only when the user needs broader coverage.
- Read only DM content that is visible in the local logged-in browser. Use `--no-dms` when the user does not want DMs processed.
- If X Chat shows passcode setup, passcode entry, or encryption-key recovery, automatically reopen X Messages in a visible browser window, wait for the user to complete it, then retry DM collection. In `--non-interactive` mode, skip DM recovery and record a data gap. The script must not choose, enter, or store the passcode.

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

- `twitter-digest/.state/config.json`: account defaults and preferences.
- `twitter-digest/.state/memory.json`: seen public post URLs, DM thread status signatures, account metadata, and run history.
- `twitter-digest/.state/daily/YYYY-MM-DD.json`: sanitized daily archive.
- `twitter-digest/.state/daily/YYYY-MM-DD.md`: sanitized markdown archive.
- `twitter-digest/.state/run/digest-input.*`: current run raw capture, including raw DM text only for immediate verification.
- `twitter-digest/.state/run/digest-context.*`: current run final summary input, including memory context and normalized facts.

Privacy rule: do not persist raw DM text in memory or daily archives. Raw DM text may exist only in the current run's private `twitter-digest/.state/run/digest-input.*` and `digest-context.*` files for immediate summarization. Use `digest-context.md` as the primary final input; use `digest-input.md` only as raw backup.

Retention and date rules:

- Seen public posts and DM thread signatures are pruned after 60 days by default.
- Sanitized daily archives are pruned after 90 days by default.
- Run dates and archive names use the user's local timezone, not UTC.

## Hotspot Detection

Cluster home timeline posts by repeated topics, hashtags, URLs, named entities, accounts, and semantic similarity. Optional keyword-search posts may be included only when the user explicitly passes `--keywords`.

A hotspot needs at least one of:

- Multiple independent posts in the digest window.
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

DMs are private. Count today's visible conversations, but summarize only unreplied conversations with real action value. Conversations that already show a self reply should not be presented as action items.

Count fields:

- `dm_visible_thread_count`: today's visible conversation targets found in the DM list.
- `dm_replied_thread_count`: today's visible conversations that appear to contain the user's reply, based on list labels such as `You:` / `You sent` / `你:`.
- `dm_unreplied_thread_count`: today's visible conversations without a detected self reply.
- `dm_captured_message_count`: captured message bubbles from opened unreplied conversations only.
- Per-thread `message_count`: captured message bubbles in that opened conversation.

Do not compare conversation counts and message counts as if they were the same unit. A user can have 5 today visible conversations, 2 unreplied conversations, and 4 captured message bubbles across those opened conversations.

Unreplied does not automatically mean important. Count every unreplied conversation, but summarize only messages that are actionable, relationship-relevant, risky, money/security-sensitive, or clearly useful. Spam, phishing, generic promotion, low-context links, and repeated junk should be classified as ignore/noise and not copied into the main narrative.

Status rules:

- `captured_unreplied_threads`: summarize the captured unreplied DM bodies selectively and classify importance.
- `no_unreplied_threads`: report the counts and say today's visible DM conversations all appear replied; do not say there are no DMs.
- `no_today_threads`: say older conversations were visible, but no today conversations were found.
- `visible_threads_unopened`: say the conversation list was visible but unreplied message bodies could not be opened; do not infer content.
- `blocked_by_x_chat_passcode`: say DM content is unavailable until the user completes X Chat passcode recovery.

Sender attribution:

- Use the thread `participant` / `会话对象` field and message bubble direction as the DM sender signal.
- Do not treat authors inside quoted posts, repost cards, link previews, or embedded tweet text as DM senders.
- If a conversation with `@jerry` contains a shared post authored by `Marco`, attribute the DM conversation to `@jerry`; mention `Marco` only as the quoted/shared post author if relevant.

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
使用 $twitter-digest 通过本地浏览器读取我最近 24 小时的 X/Twitter 动态，生成中文日报。重点总结谁 @ 了我、时间线热点、需要处理的私信或互动、我的账号动态。先给今日总结和行动建议，再给明细。回复只生成草稿，不要自动发送。读不到的数据要明确标注。
```
