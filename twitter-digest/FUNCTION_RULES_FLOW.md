# Twitter Digest Function Rules Flow

## Source Rule

`twitter-digest` is API-only.

```text
normal digest -> run_daily_digest.py -> api_x_digest.py + chat_x_digest.py -> digest_context.py
```

The wrapper uses API directly.

## Agent Rules

- For "生成X日报", "日报", "要", "继续", or similar short confirmations, run the installed `run_daily_digest.py`.
- Do not infer another source from prior conversation.
- Do not propose another collector as a fallback for missing DMs or API gaps.
- If the user asks for a non-API source, say this skill only supports API collection.

## API Configuration Flow

1. Wrapper checks saved API config.
2. If token exists, refresh it if needed.
3. If no usable token exists, open API configuration.
4. After configuration succeeds, rerun API collection.
5. If collection fails because of permission, tier, endpoint, or rate-limit issues, report the gap or failure.

OAuth authorization may open the X authorization page. No page data is collected.

## 24-Hour Window

Use the user's local timezone. Final facts must fall inside:

```text
[now - 24h, now]
```

Older mentions must not be listed as current reply tasks.

## Reply State

- `already_replied` / `handled`: do not show as pending.
- `reply_unverified`: show as `回复状态未确认`.
- Missing source: report as data gap.

## X Chat Rule

X Chat is required. If Chat configuration, collection, or decryption fails, stop the digest instead of producing a partial result or saying "没有私信".

## Privacy

Use file Read on `digest-context.md` and slices. Do not shell-print private run context during normal summarization.
