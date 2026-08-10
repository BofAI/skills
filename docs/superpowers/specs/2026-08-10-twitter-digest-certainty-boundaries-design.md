# Twitter Digest Certainty Boundaries Design

## Goal

Prevent twitter-digest from turning incomplete, stale, or indirect API evidence into a definite user-facing state. Preserve the current read-only contract, bounded X Chat requests, and concise digest output.

## Chosen Approach

Use a focused certainty-boundary update rather than a one-field patch or a broad schema rewrite.

- A minimal patch would remove only `has_message_requests`, but leave equivalent overconfident fallbacks elsewhere.
- A full typed-schema refactor would be larger than the observed problems require.
- The chosen approach removes the bad signal end to end and tightens the three adjacent inference points found in the audit.

## X Chat Message-Request Signal

Stop reading `meta.has_message_requests` in the conversation collector. Remove it from the collector return value and omit `dm_has_message_requests` from new run payloads. It must not affect counts, todo items, data gaps, scan completeness, or rendered context.

Keep one compatibility guard in `digest_context.py` that drops the legacy `message_request_pending` todo status. This prevents an old current-run file from reviving the removed behavior during an upgrade. Remove current documentation that describes the flag as a diagnostic because the application will no longer consume it.

## Other Certainty Boundaries

### Public reply state

Mark a mention as `already_replied` only when a later own post has a direct `replied_to` reference to the mention ID. A later post in the same conversation, or a later post that merely mentions the same author, is not sufficient evidence.

Incoming replies to one of the user's posts remain identified from the mention's own `replied_to` reference. If direct evidence that the user replied is absent, retain `incoming_reply` or `reply_unverified`; never upgrade it to handled through proximity or text matching.

### X Chat reply state

Accept explicit collector states `last_from_me`, `waiting_reply`, and `unknown`. For legacy input, derive a state only when `replied` is explicitly boolean. If both fields are absent or `replied` is null, use `unknown`, not `waiting_reply`.

Unknown conversations remain non-actionable historical context. Remove `requires_user_ui` and navigation instructions from newly produced unavailable-thread records; the final context may list only known participants using the existing friendly historical sentence.

### Chat authentication failure

Remove the blind second execution of the same X Chat command after HTTP 401. The command currently reuses the same token and environment, so the retry cannot repair authentication and only spends another request. Return one sanitized, actionable error saying that X Chat authorization is invalid or expired and that the user should run the existing unified configuration flow; do not expose the raw endpoint or response body.

## Compatibility and Documentation

New payloads no longer contain `dm_has_message_requests`. Context generation remains tolerant of old payloads containing that field or a legacy message-request todo, but emits neither.

Update `SKILL.md`, `DATA_COLLECTION.md`, and earlier design text that still treats the flag as meaningful. No installation command, OAuth scope, passcode flow, request budget, cache format, or write-capability rule changes.

## Tests

Regression tests must prove:

1. Conversation collection ignores `has_message_requests` and returns no request signal.
2. New Chat payloads omit `dm_has_message_requests` and contain no request todo.
3. Legacy payloads containing the field or todo still render no count, action, or message-request text.
4. Same-conversation and same-author textual proximity do not mark a mention as already replied.
5. A direct later `replied_to` reference still marks a mention as already replied.
6. A DM thread with no explicit state becomes `unknown`, while explicit boolean legacy states remain compatible.
7. Unavailable Chat history does not request UI action.
8. HTTP 401 executes the Chat collector once and produces the sanitized reconfiguration instruction; other errors keep their existing behavior.
9. The complete test suite, skill validation, and a real saved-capture compatibility check pass.

## Non-Goals

- Inferring hidden message requests through another endpoint or browser UI.
- Expanding X Chat scan limits or changing rate-limit behavior.
- Reworking public API pagination, like semantics, or digest section layout.
- Adding reply suggestions or any posting, liking, accepting, or messaging capability.
