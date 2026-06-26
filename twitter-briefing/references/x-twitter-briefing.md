# X/Twitter Briefing Reference

Use this reference when implementing, auditing, or troubleshooting a Codex, Claude, or other agent workflow that reads a user's own X/Twitter data.

## Access Patterns

Prefer the least-complex path that can actually provide the requested data.

### Recommended no-developer-API setup

For ordinary users who do not want an X developer account:

1. Use direct local browser automation with a persistent Chrome profile for live visible X data such as mentions, keyword searches, home timeline hotspots, own activity, and approved visible DMs.
2. Use the official X archive for DMs and historical account data. X states the archive includes JSON/HTML account data, including posts and Direct Messages.
3. Use cookie-based MCP only as a fallback if direct browser automation is unavailable.
4. Combine sources in the final brief. State which source each section used.

This is the practical default because public mentions and hotspots need live access, while private DMs should not be handed to random public scraping services.

### Direct Browser Automation

Use `scripts/browser_x_briefing.py` first. It launches a dedicated Chrome profile at `~/.twitter-briefing/chrome-profile`, opens `x.com`, waits for the user to log in once, then reuses that saved browser profile on later runs.

The intended interaction is chat-only:

1. User asks in chat for an X daily brief.
2. Agent runs `scripts/run_daily_brief.py`.
3. On first use only, user logs in inside the opened dedicated browser window.
4. Agent reads `/tmp/x-briefing/briefing-input.md`.
5. Agent replies with the Chinese daily brief.
6. Later requests skip login and reuse `~/.twitter-briefing/chrome-profile`.

Do not require the user to copy cookies, configure MCP, restart the app, or run commands manually.

Typical run:

```bash
python3 twitter-briefing/scripts/run_daily_brief.py
```

If handle auto-detection fails:

```bash
python3 twitter-briefing/scripts/browser_x_briefing.py \
  --handle your_handle \
  --out /tmp/x-briefing
```

If the user explicitly approves local DM processing:

```bash
python3 twitter-briefing/scripts/browser_x_briefing.py \
  --include-dms \
  --out /tmp/x-briefing
```

Outputs:

- `/tmp/x-briefing/briefing-input.json`
- `/tmp/x-briefing/briefing-input.md`
- `/tmp/x-briefing/memory-context.json`
- `/tmp/x-briefing/memory-context.md`

Memory files:

- `~/.twitter-briefing/config.json`: account defaults and user preferences.
- `~/.twitter-briefing/memory.json`: seen public post IDs/URLs, DM thread status signatures, account metadata, and run history.
- `~/.twitter-briefing/daily/YYYY-MM-DD.json`: sanitized daily archive.
- `~/.twitter-briefing/daily/YYYY-MM-DD.md`: sanitized markdown archive.

Privacy rule: do not persist raw DM text in memory or daily archives. Raw DM text may exist only in the current run's `/tmp/x-briefing/briefing-input.*` files for immediate summarization. Use `memory-context.md` to distinguish new, repeated, and unchanged items in the final Chinese brief.

Browser collection rules:

- Use a dedicated profile, not the user's normal Chrome profile.
- Login state is persisted under `~/.twitter-briefing/chrome-profile`.
- Do not post, like, follow, accept DM requests, open suspicious links, or reply.
- Keep scrolling bounded. Increase `--scrolls` only when the user needs broader coverage.
- If X shows a login page, wait for the user to log in; do not automate password entry.
- If X shows CAPTCHA or account challenge, stop and ask the user to resolve it manually.
- DM reading is limited to message content visible in the local browser. If X Chat shows a passcode setup or end-to-end-encryption onboarding screen, the script records `dm_status=blocked_by_x_chat_passcode`; the user must complete that X Chat setup in the browser once before DM conversations are readable.

### Cookie-Based MCP Fallback

Use `agent-twitter-client-mcp` only as a fallback. It uses the user's logged-in X cookies instead of X developer API credentials. The MCP setup uses:

```json
{
  "mcpServers": {
    "twitter": {
      "command": "npx",
      "args": ["-y", "agent-twitter-client-mcp"],
      "env": {
        "AUTH_METHOD": "cookies",
        "TWITTER_COOKIES": "[\"auth_token=...; Domain=.twitter.com\", \"ct0=...; Domain=.twitter.com\", \"twid=...; Domain=.twitter.com\"]"
      }
    }
  }
}
```

Generate this template from the skill with:

```bash
python3 twitter-briefing/scripts/generate_xactions_mcp_config.py --client generic
```

For Claude Desktop config JSON:

```bash
python3 twitter-briefing/scripts/generate_xactions_mcp_config.py --client claude-desktop
```

For guided setup on this machine:

```bash
python3 twitter-briefing/scripts/setup_xactions_mcp.py --client codex --browser-login
```

For guided Claude Desktop setup:

```bash
python3 twitter-briefing/scripts/setup_xactions_mcp.py --client claude-desktop --browser-login
```

The guided setup opens a dedicated browser window, waits for the user to log in to X, reads the local `x.com` `auth_token` through the browser DevTools endpoint, then writes `~/.codex/config.toml` after creating a timestamped backup. The token is not printed in terminal output or conversation logs.

The setup script obtains `auth_token`, `ct0`, and `twid` from the user's own logged-in `x.com` browser session. Treat these cookies like passwords:

- Never commit it.
- Prefer storing it in the MCP host's local secret/config mechanism.
- Do not paste it into shared chats.
- Use read-only analysis workflows unless the user explicitly asks for write actions.
- Warn that browser-session automation can be fragile and may be affected by X product changes or account automation controls.

Useful `agent-twitter-client-mcp` tool capabilities for this skill:

- `search_tweets`
- `get_user_tweets`
- `get_tweet_by_id`
- `get_user_profile`
- `get_followers`
- `get_following`

Do not rely on the local MCP for private DMs unless the installed tool version explicitly exposes a read-DM tool and the user has approved private-message processing.

### Browser-session operating flow

Use this flow for daily briefing runs:

1. Run `browser_x_briefing.py` and collect `/tmp/x-briefing/briefing-input.md`.
2. Review captured pages: `home`, `mentions_search`, `mentions_notifications`, keyword search pages, and optionally `messages`.
3. Use captured `article` text, status URLs, timestamps, and visible page text as source evidence.
4. Analyze with this skill's importance scoring and daily summary format.
5. If DMs are needed and browser capture is insufficient, ask for an official X archive and run `parse_x_archive.py`.

Keep browser-session use human-paced. Avoid bulk write actions, auto-following, auto-liking, or mass messaging as part of this briefing skill.

### Official X archive

Use this when the user wants no developer API and needs DMs or private historical account data.

User steps:

1. Open X settings.
2. Go to `Your account`.
3. Select `Download an archive of your data`.
4. Confirm password and identity code.
5. Request the archive.
6. When X emails/notifies that it is ready, download the `.zip`.
7. Run `scripts/parse_x_archive.py` against the `.zip`.

Limitations:

- The archive is not real-time and may take time to prepare.
- It is a snapshot, so it is suitable for historical summaries and periodic reviews, not instant alerting.
- It may not contain all public mentions from other people; use live search/MCP for mentions.

### Managed third-party MCP

Use TwitterAPI.io, Octolens, OpenTweet, or similar when the user wants a fast setup and accepts a third-party service. These can avoid an X developer account, but they usually use their own API key/subscription and may not provide private DMs.

Good fit:

- Public mentions.
- Keyword monitoring.
- Hotspot search.
- Brand monitoring.

Poor fit:

- Private DMs.
- Full personal account export.
- Workflows requiring guaranteed official write/DM semantics.

### Official X API

Use official X API only when the user wants production reliability, official OAuth, DM read/write scopes, or account actions that should not depend on browser session behavior.

Minimum useful read capabilities:

- `get_me`: return authenticated user id and username.
- `search_mentions` or `search_recent_posts`: find posts that mention `@username`.
- `get_reposts_of_me`: find reposts of the authenticated user's posts, if available.
- `get_home_timeline`: read the authenticated user's reverse-chronological timeline for hotspot analysis.
- `list_dm_conversations` and `get_dm_events`: read recent direct-message conversations, if the user's X access tier and scopes allow it.
- `get_post` / `get_user`: hydrate author, engagement, timestamp, and URL fields.

If only exported data is available, parse it as an offline snapshot and state that live mentions, DMs, and trend velocity may be incomplete.

## X API Notes

X API capabilities depend on the developer account tier, app type, OAuth scopes, and endpoint access. Verify the current docs before finalizing a production integration.

Common endpoint families for this workflow:

- Authenticated user: `GET /2/users/me`.
- Timeline: `GET /2/users/{id}/timelines/reverse_chronological`.
- Mentions: search recent posts for `@username`, or use user mention endpoints if exposed by the selected API tier/tool.
- Reposts of me: `GET /2/users/{id}/retweeted_by` style lookups may vary by tool; use the connector's documented method.
- Direct messages: `GET /2/dm_conversations/{id}/dm_events` and related DM conversation endpoints when permitted.

Common OAuth scopes to check:

- `tweet.read`
- `users.read`
- `offline.access` for refresh tokens
- `dm.read` for reading direct messages

Use write scopes only when the user explicitly wants the agent to draft and send posts or messages:

- `tweet.write`
- `dm.write`
- `like.write`
- `follows.write`

Default to read-only scopes for a briefing workflow.

## MCP Connector Guidance

For agent hosts such as Codex, Claude, or another MCP-compatible client, the clean production shape is:

1. User authorizes X through OAuth in the connector or a companion setup flow.
2. Connector stores tokens securely outside the prompt context.
3. The agent calls connector tools to fetch structured data.
4. Connector returns only the fields needed for analysis.
5. The agent produces a summary and drafts, but does not take write actions without confirmation.

Tool outputs should include stable ids, canonical URLs, timestamps, author handles, follower count if available, engagement metrics, and text. Do not return raw OAuth tokens, cookies, or full private archives when a narrowed query will do.

## Importance Scoring

Score each item from 0 to 100. Use the score to rank, not as a false precision claim.

Suggested weights:

- Direct action requested: +25
- Time sensitivity or deadline: +20
- Reputation, security, legal, finance, or customer risk: +20
- High-relevance relationship or business opportunity: +15
- High-signal author or engagement: +10
- Repeated topic across independent sources: +10
- Spam, vague tag, automated promo, or low-context mention: -20
- Harassment, phishing, or obvious scam: classify separately as risk/ignore and avoid amplifying.

Classification bands:

- 80-100: urgent
- 60-79: important
- 35-59: routine
- 0-34: ignore/noise

## Hotspot Detection

Cluster home timeline posts by repeated topics, hashtags, URLs, named entities, accounts, and semantic similarity. Optional keyword-search posts may be included only when the user explicitly passes `--keywords`. A hotspot needs at least one of:

- Multiple independent posts in the briefing window.
- One high-signal post with unusually strong engagement.
- A topic that directly affects the user's projects, brand, customers, portfolio, or community.

For each hotspot, include:

- Topic name.
- Why it is surfacing now.
- Evidence from 2-4 representative posts when available.
- User relevance.
- Suggested action: monitor, reply, quote, DM, ignore, or investigate.

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

使用这个中文 prompt 进行每日运行：

```text
使用 $twitter-briefing 读取我最近 24 小时的 X/Twitter 动态，生成中文日报。重点总结谁 @ 了我、圈内热点、需要处理的私信或互动、我的账号动态。先给今日总结和行动建议，再给明细。回复只生成草稿，不要自动发送。读不到的数据要明确标注。
```

业务账号版本：

```text
使用 $twitter-briefing 生成今天的 X/Twitter 中文运营简报。优先看客户问题、媒体/KOL 提及、合作机会、舆情风险和重要私信。给出处理建议和回复草稿，但不要发送任何内容。
```
