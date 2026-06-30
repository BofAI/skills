# X/Twitter Digest Reference

Use this reference when implementing, auditing, or troubleshooting the X/Twitter digest workflow.

## Access Model

The preferred public-data layer is the hosted X MCP installed in the AI client. The agent calls X MCP tools directly for authenticated user lookup, home timeline, mentions, own posts, recent search, trends/news/articles when relevant, and optional keyword searches. Do not add a local MCP wrapper script for normal public-data collection.

The local scripts are now browser DM infrastructure:

- `scripts/collect_browser_dm.py`: command-line wrapper for visible X Chat/DM collection. It writes `browser-dm-context.md/json`.
- `lib/browser_dm_core.py`: internal browser/CDP implementation used by `collect_browser_dm.py`.

X MCP setup:

```bash
npm install -g @xdevplatform/xurl
xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
xurl auth oauth2 --app my-app
xurl auth default my-app
```

Codex config:

```toml
[mcp_servers.xapi]
command = "xurl"
args = ["mcp", "https://api.x.com/mcp"]

[mcp_servers.x-docs]
url = "https://docs.x.com/mcp"
```

Browser mode:

- The user logs in to X once in the dedicated browser profile.
- Later runs default to headless collection and reuse the saved browser session.
- If saved login is unavailable and interactive mode is allowed, the script opens a visible browser window for manual login.
- If X Chat asks for passcode setup, passcode entry, or encryption-key recovery and interactive mode is allowed, the script opens or reuses a visible browser window, waits for completion, then retries DM collection.
- The script reads visible content from X pages.

X MCP mode:

- Intended for stable public/account data collection through AI tool calls.
- Requires X MCP to be installed and authenticated through `xurl`.
- The user enters Client ID and Client Secret in the local terminal during `xurl auth apps add`; do not ask the user to paste secrets into chat. If the agent can open a visible local terminal window, it should do that and let the user type credentials there instead of only printing setup commands.
- App-only keys are not enough for user-context home timeline reliability; use OAuth user-context via `xurl auth oauth2`.
- Do not use cookie-based Twitter MCP servers such as `agent-twitter-client-mcp`; they are outside this skill's supported collection path.
- Normal daily runs use X MCP for public data and browser collection for DMs. DM/X Chat lookup through API/MCP may be incomplete, so browser DM remains authoritative.
- MCP tool failures should be reported as data gaps, not silently treated as empty pages.

Chat-triggered X MCP setup:

```bash
npm install -g @xdevplatform/xurl
xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
xurl auth oauth2 --app my-app
xurl auth default my-app
```

Then add the MCP server to the AI client config and restart the client. The user should only enter credentials in the local terminal and X OAuth browser page.

Agent-assisted desktop setup:

1. Open a visible terminal window for `xurl auth apps add`.
2. Let the user type Client ID and Client Secret locally; hide Secret input when possible.
3. Run `xurl auth oauth2 --app APP_NAME` so the browser OAuth page opens.
4. Verify `xurl auth status` and set the default app/user.
5. Write `xapi` MCP config and tell the user to restart the AI client.

Typical chat run:

1. Call X MCP tools for public/account facts.
2. Run `collect_browser_dm.py` only if DM/X Chat coverage is needed.
3. Merge those facts in the final Chinese summary.

Force a visible browser window for debugging:

```bash
python3 twitter-digest/scripts/collect_browser_dm.py --headed
```

For unattended scheduled runs that should not open a visible browser:

```bash
python3 twitter-digest/scripts/collect_browser_dm.py --non-interactive
```

Browser DM collection:

```bash
python3 twitter-digest/scripts/collect_browser_dm.py
```

Browser DM outputs:

- `twitter-digest/.state/run/browser-dm-context.json`: raw machine-readable browser DM context.
- `twitter-digest/.state/run/browser-dm-context.md`: readable browser DM context. Use this for DM/browser facts, not as a replacement for X MCP public facts.

## Browser Collection Rules

- Use the dedicated profile, not the user's normal browser profile.
- Do not ask the user to copy cookies or tokens.
- If X shows a login page, wait for the user to log in manually.
- If X shows CAPTCHA or account challenge, stop and ask the user to resolve it in the browser.
- Do not post, like, follow, accept DM requests, open suspicious links, or reply.
- Read only DM content that is visible in the local logged-in browser.
- If X Chat shows passcode setup, passcode entry, or encryption-key recovery, wait for the user to complete it in the visible browser window, then retry DM collection. In `--non-interactive` mode only, record a data gap and continue. The script must not choose, enter, or store the passcode.

## Pages Collected

The browser collector opens only:

- `messages`: X Messages / X Chat.

## Run Outputs

Current-run files:

- `twitter-digest/.state/run/browser-dm-context.md`: readable browser DM context.
- `twitter-digest/.state/run/browser-dm-context.json`: machine-readable browser DM context.

Privacy rule: do not write long-term memory, daily archives, API token caches, or public MCP captures. Raw DM text may exist only in the current run's private `browser-dm-context.*` files for immediate summarization/debugging.

Date rule:

- Run dates use the user's local timezone, not UTC.

## Hotspot Detection

Cluster home timeline posts by repeated topics, hashtags, URLs, named entities, accounts, and semantic similarity. Optional keyword-search posts may be included when the user explicitly asks for those searches.

For MCP-backed runs, public timeline, profile, mentions, and search facts come from X MCP. The browser collector is not the public-data source.

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

For waiting-reply DMs that should be summarized, `browser-dm-context.md` includes loaded message history, raw thread label, URL, and load metadata. It can include up to 2000 loaded message bubbles per thread. Use it to understand the conversation, but do not copy full private history into the final digest. Keep final DM summaries short and action-oriented.

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
