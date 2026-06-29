# X/Twitter Digest Reference

Use this reference when implementing, auditing, or troubleshooting the X/Twitter digest data collection workflow.

## Access Model

The data collection layer has three scripts:

- `scripts/browser_x_digest.py`: local browser collector. It launches a dedicated Chromium profile at `twitter-digest/.state/chrome-profile`, reads X page DOM, and is required for X Chat / DM content.
- `scripts/api_x_digest.py`: official API collector. It uses saved OAuth2 user-context credentials, `X_BEARER_TOKEN` / `TWITTER_BEARER_TOKEN`, or `--bearer-token` and writes the same `digest-input.*` shape as the browser collector.
- `scripts/run_daily_digest.py`: upper wrapper. Default `--source auto` uses API when configured, otherwise browser.

Browser mode:

- The user logs in to X once in the dedicated browser profile.
- Later runs default to headless collection and reuse the saved browser session.
- If saved login is unavailable, the script opens a visible browser window for manual login.
- The script reads visible content from X pages.

API mode:

- Intended for stable public-data collection.
- Requires user-context authorization for user-owned timelines. App-only keys are not enough for home timeline reliability.
- Reads the official reverse chronological home timeline when the token has user-context timeline access.
- Normal daily runs use browser collection for DMs. API DM lookup is retained only as TODO/debug because XChat / encrypted messages may not appear in `/2/dm_events`.
- Records endpoint-level API failures as data gaps instead of silently treating them as empty pages.
- DM lookup failures, zero-event API responses, and inconclusive API DM results are recorded as `api_dm_todo`; do not summarize them as empty inboxes. Use browser collection for X Chat / encrypted DMs while waiting for X to fix or document reliable API coverage.
- Saved OAuth tokens are configured by the agent-triggered `run_daily_digest.py --configure-api` flow. OAuth2 PKCE is the supported path for user-owned local X Apps: the user provides the Client ID, authorizes the app in the browser, and the script saves the access token plus refresh token. OAuth2 tokens are refreshed automatically when a refresh token is saved.

Chat-triggered API setup:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --configure-api
```

The user should only interact with the system prompts and X OAuth browser page. Do not require the user to export env vars or paste tokens into shell history.

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

Force a data source:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --source browser
X_BEARER_TOKEN=... python3 twitter-digest/scripts/run_daily_digest.py --source api --handle <handle>
```

Outputs:

- `twitter-digest/.state/run/digest-input.json`: raw collector capture.
- `twitter-digest/.state/run/digest-input.md`: readable raw collector capture.
- `twitter-digest/.state/run/digest-context.json`: normalized current-run facts.
- `twitter-digest/.state/run/digest-context.md`: primary final summary input. Read this first.

Collector comparison testing:

```bash
python3 twitter-digest/scripts/compare_collectors.py --rounds 3 --interval-sec 120
```

One round means one complete public-data API collection plus one complete browser collection. The comparison runner keeps per-round raw outputs and writes `comparison-report.md/json` under `twitter-digest/.state/compare-runs/<timestamp>/`. It enforces a minimum 120-second delay between rounds to reduce API rate-limit risk. Read `COLLECTOR_COMPARISON_TEST.md` before interpreting these reports. Browser DM remains authoritative; API DM is intentionally not tested.

## Browser Collection Rules

- Use the dedicated profile, not the user's normal browser profile.
- Do not ask the user to copy cookies or tokens.
- If X shows a login page, wait for the user to log in manually.
- If X shows CAPTCHA or account challenge, stop and ask the user to resolve it in the browser.
- Do not post, like, follow, accept DM requests, open suspicious links, or reply.
- Keep scrolling bounded by the digest goal. Public pages default to `--scrolls 40`, `--max-public-items 300`, and `--public-window-hours 24`, stopping early when loaded post timestamps are clearly outside the daily window.
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

## Run Outputs

Current-run files:

- `twitter-digest/.state/config.json`: account defaults and preferences.
- `twitter-digest/.state/run/digest-context.md`: the only normal input for AI daily-summary writing.
- `twitter-digest/.state/run/digest-context.json`: machine-readable current-run facts.
- `twitter-digest/.state/run/digest-input.*`: raw collector capture for debugging only.

Privacy rule: do not write long-term memory or daily archives. Raw DM text may exist only in the current run's private `twitter-digest/.state/run/digest-input.*` and `digest-context.*` files for immediate summarization/debugging. Use only `digest-context.md` for normal final summaries.

Date rule:

- Run dates use the user's local timezone, not UTC.

## Hotspot Detection

Cluster home timeline posts by repeated topics, hashtags, URLs, named entities, accounts, and semantic similarity. Optional keyword-search posts may be included only when the user explicitly passes `--keywords`.

Public timeline, profile, and mentions collection follows the same bounded-window model as DM collection: load enough context for a 24-hour digest, cap the amount passed to the model, and stop early when timestamps show older content. Treat public item counts as browser-loaded items in this run, not exhaustive X history.

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

DMs are private. Count today's visible conversations, but summarize only conversations whose latest preview is not from the user and has real action value. Conversations whose latest preview is `You:` / `You sent` / `你:` should not be presented as action items.

Count fields:

- `dm_visible_thread_count`: today's visible conversation targets found in the DM list.
- `dm_replied_thread_count`: today's visible conversations whose latest list preview appears to be from the user, based on labels such as `You:` / `You sent` / `你:`.
- `dm_unreplied_thread_count`: today's visible conversations waiting for the user's reply, meaning the latest list preview is not from the user.
- `dm_captured_message_count`: captured message bubbles from opened waiting-reply conversations only.
- Per-thread `message_count`: captured message bubbles in that opened conversation.

Do not compare conversation counts and message counts as if they were the same unit. A user can have 5 today visible conversations, 2 waiting-reply conversations, and 4 captured message bubbles across those opened conversations.

The collector opens waiting-reply conversations and scrolls upward before extracting message bubbles. Defaults are `--dm-scrolls 200`, `--dm-max-messages 2000`, and `--dm-window-hours 0`, so it tries to load the full browser-available thread instead of stopping at the 24-hour digest window. If X does not reach the thread top or the message cap is hit, the context records `dm_thread_incomplete`.

Waiting-reply does not automatically mean important. Count every waiting-reply conversation, but summarize only messages that are actionable, relationship-relevant, risky, money/security-sensitive, or clearly useful. Spam, phishing, generic promotion, low-context links, and repeated junk should be classified as ignore/noise and not copied into the main narrative.

For waiting-reply DMs that should be summarized, `digest-context.md` includes a `### DM Thread Context` section with loaded message history, raw thread label, URL, and load metadata. It can include up to 2000 loaded message bubbles per thread. Use it to understand the conversation, but do not copy full private history into the final digest. Keep final DM summaries short and action-oriented.

Media/link context:

- Public items may include `media`, `link`, and `card` lines with image/video URLs, thumbnail URLs, alt text, shared-post links, or external links.
- DM message context may include per-message `link:` and `media:` lines.
- Use these fields to understand whether a post or DM includes a shared post, image, video, or external reference.
- Do not open suspicious links. Do not claim visual details that are not present in the text, alt text, thumbnail URL, or surrounding context.

Status rules:

- `captured_unreplied_threads`: summarize the captured waiting-reply DM bodies selectively and classify importance.
- `no_unreplied_threads`: report the counts and say today's visible DM conversations all have latest previews from the user; do not say there are no DMs.
- `no_today_threads`: say older conversations were visible, but no today conversations were found.
- `visible_threads_unopened`: say the conversation list was visible but waiting-reply message bodies could not be opened; do not infer content.
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
