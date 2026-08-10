# Twitter Digest Rate-Limit Diagnostics Design

## Goal

Release `v1.5.14-beta.11` with accurate, privacy-safe X Chat rate-limit diagnostics across normal digest collection and first-time configuration.

## Scope

- Preserve the X Chat endpoint category, HTTP status, and retry delay across the collector-to-wrapper process boundary.
- Normalize event paths to `/chat/conversations/:id/events`; never expose a conversation ID.
- Translate endpoint categories into concise Chinese user messages.
- Stop immediately on HTTP 429 in both normal X Chat collection and X Chat configuration.
- Record per-endpoint request counts for conversations, events, and public keys in successful X Chat output.
- Keep request counts internal unless the user asks for statistics or a failure needs diagnosis.
- Preserve all `beta.10` safe-scan limits and read-only restrictions.

## Architecture

`chat_x_digest.py` remains the source of truth for runtime Chat requests. It will normalize request paths, track per-route counts, and emit a machine-readable error marker containing only a route category, status, and optional retry delay. `collector_commands.py` will recognize that marker before its legacy keyword summarization and produce a stable diagnostic string. `run_daily_digest.py` will convert that diagnostic into a friendly Chinese message without exposing identifiers.

`configure_chat.py` uses a separate request helper, so it will adopt the same route normalization and error marker format. It will treat 429 as terminal on the first response while retaining retry behavior for transient non-429 failures.

## Endpoint Categories

| Normalized route | Internal category | User wording |
|---|---|---|
| `/chat/conversations` | `conversation_list` | `X Chat 会话列表暂时受到限流` |
| `/chat/conversations/:id/events` | `conversation_events` | `X Chat 消息读取暂时受到限流` |
| `/users/:id/public_keys` | `public_keys` | `X Chat 公钥读取暂时受到限流` |

Unknown Chat paths use category `x_chat_other` and wording `X Chat 接口暂时受到限流`.

## Error Contract

The child collector writes one stderr line in this format:

```text
TWITTER_DIGEST_API_ERROR {"source":"x_chat","endpoint":"conversation_events","status":429,"retry_after_seconds":317}
```

Only allowlisted fields are serialized. Raw response bodies, access tokens, user IDs, conversation IDs, and URLs are excluded. Legacy plain-text errors remain supported as a fallback.

The final user-facing message is:

```text
X Chat 消息读取暂时受到限流，预计约 6 分钟后恢复。请稍后再生成日报。
```

If no recovery time is available, omit the estimate. Seconds are rounded up to whole minutes, with a minimum of one minute.

## Request Statistics

Successful Chat output adds:

```json
{
  "dm_api_request_counts": {
    "conversation_list": 1,
    "conversation_events": 6,
    "public_keys": 0
  }
}
```

Counts represent actual HTTP attempts, including failed attempts and retries. Existing `dm_event_request_count` remains the logical event-call budget counter for compatibility; it can be lower than `conversation_events` when an individual call succeeds after a transient retry.

## Configuration Behavior

The initial Chat key setup may call `/users/:id/public_keys` with `juicebox_config`. A 429 response stops immediately and uses the same friendly endpoint-specific diagnostic. OAuth authorization and token refresh behavior are unchanged.

## Tests and Acceptance Criteria

- A collector 429 error retains the normalized endpoint category and retry delay through the wrapper.
- A concrete conversation ID never appears in the summarized or user-facing error.
- Configuration performs exactly one HTTP attempt after a 429.
- Non-429 transient configuration failures retain their existing bounded retry behavior.
- Successful output contains correct per-category request counts.
- Existing safe-scan, public-key cache, read-only, installer, and security tests continue to pass.
- Codex and Claude clean/upgrade installation from the published tag both contain `beta.11` code.

## Out of Scope

- Persistent request logs.
- Sending telemetry to a remote service.
- Changing X API credentials, scopes, or read-only guarantees.
- Increasing collection budgets to trade reliability for completeness.
