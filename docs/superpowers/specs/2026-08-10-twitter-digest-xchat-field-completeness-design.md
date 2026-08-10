# Twitter Digest X Chat Field and Completeness Design

## Goal

Make X Chat collection follow the official Chat XDK response contract and prevent the collector from silently omitting messages or claiming a complete scan when it stopped at a safe boundary.

The change must preserve the existing read-only security contract and the protections that reduce HTTP 429 responses.

## Root Causes

The current collector sends field-selection parameters that the official Chat XDK examples do not use. In particular, the public-key route explicitly returns all public-key fields and does not accept `public_key.fields`.

The collector also filters encrypted events by a raw API timestamp before decryption. The official event contract requires `encoded_event`, while the useful `created_at_msec` value is available in the decrypted Chat XDK event. A raw event without a timestamp can therefore contain a valid recent message but currently never reaches the decryptor.

Conversation-list completeness is tracked separately from event scanning. When the configured conversation limit is reached while `meta.next_token` is present, the current collector loses that pagination state and can report a complete scan. The three-consecutive-old-conversation optimization also depends on an ordering guarantee that is not part of the public X Chat contract.

## Request Contract

Public-key requests use only:

```text
GET /2/users/{id}/public_keys
```

No `public_key.fields` parameter is sent during configuration or normal collection. The existing mapping into Chat XDK remains unchanged:

- API `signing_public_key` becomes SDK `public_key`.
- API `public_key` becomes SDK `identity_public_key`.
- API `identity_public_key_signature` is passed through.
- `juicebox_config` is used only while configuring the authenticated account.

Conversation-event requests send only `max_results` and an optional `pagination_token`. The collector consumes `data[].encoded_event`, optional `sender_id` and `id`, and `meta.next_token`. Optional response fields may improve diagnostics but must never be required for decryption.

The conversation-list request stops asking for `updated_at`. Participant expansions remain defensive because observed X Chat responses may identify members through either `participant_ids` or `member_ids`.

## Event Processing

Every non-empty `encoded_event` from fetched event pages is eligible for Chat XDK decryption, even when the raw API item has no timestamp. Raw timestamps may be used only as a pagination hint.

After decryption, the collector obtains message type, sender, content, verification state, and `created_at_msec` from the decrypted event. It then applies the requested time window. If a decrypted message lacks a usable timestamp, it is excluded from time-bounded facts and reported as a data gap; it is not treated as an empty conversation.

Raw event metadata is retained only as a fallback for SDK versions that omit a corresponding decrypted field. A missing raw-to-decrypted event association must not discard a decrypted message when the decrypted event itself contains the required timestamp.

## Completeness Accounting

Conversation collection returns both the collected conversations and whether another list page exists. If `meta.next_token` remains after the configured maximum is reached, the final result records an incomplete conversation-list scan.

The existing limits remain:

- At most 20 event requests per run.
- Reserve the final 5 requests reported by X.
- At most 3 event pages per conversation.
- Stop after 3 consecutive conversations whose newest known event predates the requested window.

These boundaries protect the account from rate limits. Reaching any boundary produces an incomplete-scan result with the number of conversations checked. It never implies that unscanned conversations have no recent messages.

Because X does not publicly guarantee conversation-list ordering, the consecutive-old stop remains a best-effort boundary rather than evidence that all later conversations are old.

Conversations with missing IDs are counted as unscannable. Missing participants affect only the friendly label, not whether events are fetched. A missing optional field is always represented as unknown or incomplete, never false or empty.

## User-Facing Behavior

Normal successful output remains concise. When the safe scan is incomplete, the digest says only:

```text
X Chat 已检查最近的 N 个会话。
```

It does not expose budgets, internal field names, raw API paths, user IDs, conversation IDs, or response bodies.

The conversation-list message-request marker is ignored because it does not identify a sender, expose content, or prove that a request is currently visible in X. It never creates a count, todo, or X-interface action.

The skill remains permanently read-only and never accepts requests, replies, sends messages, or creates a script to do so.

## Tests

Regression tests will prove that:

1. Public-key requests do not send `public_key.fields` in configuration or collection.
2. Event requests do not send `chat_message_event.fields`.
3. An encrypted event without a raw timestamp is still passed to Chat XDK and retained when its decrypted event has an in-window `created_at_msec`.
4. An event with neither a usable raw nor decrypted timestamp becomes a data gap rather than a false empty-inbox result.
5. A conversation-list `next_token` left at the 50-conversation boundary marks the scan incomplete.
6. Missing conversation IDs mark the scan incomplete.
7. The event-request budget, rate-limit reserve, per-conversation page cap, and old-conversation stop still work.
8. Existing digest presentation, read-only security, installer, and configuration tests remain green.

## Non-Goals

- Scanning every historical conversation regardless of rate limits.
- Relying on undocumented ordering to claim completeness.
- Adding another X data source, browser scraping, cookies, or legacy DM endpoints.
- Changing the digest's authorization scopes or enabling any write capability.
