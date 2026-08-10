# Twitter Digest X Chat Field and Completeness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align X Chat requests with the official Chat XDK contract and prevent valid encrypted messages or unscanned conversations from being reported as absent.

**Architecture:** Keep the current bounded collector, but separate raw encrypted-event acquisition from post-decryption time filtering. Return explicit conversation-list completeness metadata and combine it with event-scan completeness in the final payload.

**Tech Stack:** Python 3.10+, standard-library `unittest`, `unittest.mock`, official `chatxdk==0.4.3` runtime.

## Global Constraints

- Keep twitter-digest permanently read-only; add no posting, replying, liking, following, accepting, or DM-sending capability.
- Keep the event ceiling at 20 requests, rate-limit reserve at 5, page ceiling at 3 per conversation, and consecutive-old boundary at 3.
- Do not expose raw API paths, response bodies, conversation IDs, user IDs, or request-budget internals in normal digest prose.
- Treat missing optional X Chat fields as unknown or incomplete, never as false or empty.
- Do not modify unrelated existing `twitter-mcp` worktree changes.

---

### Task 1: Minimal X Chat Request Fields

**Files:**
- Modify: `twitter-digest/tests/test_chat_x_digest.py`
- Modify: `twitter-digest/tests/test_configure_chat.py`
- Modify: `twitter-digest/scripts/chat_x_digest.py:180-280`
- Modify: `twitter-digest/scripts/configure_chat.py:155-158`

**Interfaces:**
- Consumes: existing `api_get(token, path, params=None)` in both scripts.
- Produces: public-key requests with no query dictionary and event requests containing only `max_results` plus an optional `pagination_token`.

- [ ] **Step 1: Write failing request-contract tests**

Add tests that capture the arguments passed to `api_get` and assert literal request contracts:

```python
def test_fetch_signing_keys_does_not_send_unsupported_field_selector(self):
    with mock.patch.object(chat_x_digest, "api_get", return_value={"data": []}) as api_get:
        chat_x_digest.fetch_user_signing_keys("token", "42")
    self.assertEqual(api_get.call_args.args, ("token", "/users/42/public_keys"))

def test_collect_events_requests_only_pagination_controls(self):
    with mock.patch.object(chat_x_digest, "api_get", return_value={"data": [], "meta": {}}) as api_get:
        chat_x_digest.collect_events("token", "c", cutoff, chat_x_digest.EventRequestBudget(20))
    self.assertEqual(api_get.call_args.args[2], {"max_results": 100, "pagination_token": ""})
```

Update the configuration test to expect `/users/secret-user/public_keys` with no `public_key.fields` query string.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
python3 -m unittest twitter-digest/tests/test_chat_x_digest.py twitter-digest/tests/test_configure_chat.py -v
```

Expected: failures show the existing `public_key.fields`, `chat_message_event.fields`, and configuration query string.

- [ ] **Step 3: Implement the minimal request changes**

Remove `public_key.fields` from normal and configuration public-key calls. Remove `chat_message_event.fields` from event calls. Remove `updated_at` from the conversation field selector while retaining participant/member expansions and user includes.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the Step 2 command. Expected: all focused tests pass.

- [ ] **Step 5: Commit the request-contract fix**

```bash
git add twitter-digest/scripts/chat_x_digest.py twitter-digest/scripts/configure_chat.py twitter-digest/tests/test_chat_x_digest.py twitter-digest/tests/test_configure_chat.py
git commit -m "fix(twitter-digest): align X Chat request fields"
```

### Task 2: Decrypt Before Applying the Time Window

**Files:**
- Modify: `twitter-digest/tests/test_chat_x_digest.py`
- Modify: `twitter-digest/scripts/chat_x_digest.py:425-493`

**Interfaces:**
- Consumes: raw event dictionaries with required `encoded_event` and optional raw timestamp; Chat XDK rows containing `event.created_at_msec`.
- Produces: a helper `message_time(decrypted_event: dict[str, Any], raw_event: dict[str, Any]) -> datetime | None` and message extraction that filters only after decryption.

- [ ] **Step 1: Write failing timestamp-fallback tests**

Add literal tests proving decrypted time has priority and raw time remains a fallback:

```python
def test_message_time_uses_decrypted_created_at_msec_without_raw_timestamp(self):
    value = chat_x_digest.message_time({"created_at_msec": 1786320000000}, {})
    self.assertEqual(value, dt.datetime.fromtimestamp(1786320000, tz=dt.timezone.utc))

def test_message_time_falls_back_to_raw_event_timestamp(self):
    value = chat_x_digest.message_time({}, {"created_at": "2026-08-10T00:00:00Z"})
    self.assertEqual(value, dt.datetime(2026, 8, 10, tzinfo=dt.timezone.utc))
```

Add a collector-level test with a fake Chat object: a raw item contains only `encoded_event`, while its decrypted event contains an in-window `created_at_msec`. Assert the encrypted blob reaches `decrypt_events` and the output thread contains the message.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
python3 -m unittest twitter-digest/tests/test_chat_x_digest.py -v
```

Expected: `message_time` is missing and the collector-level case produces no readable message.

- [ ] **Step 3: Implement decrypt-first processing**

Build `decryptable_events` from every raw event whose `encoded_event` is non-empty. Do not use raw time in this selection. Feed all fetched encrypted events to Chat XDK, then use `message_time(event, raw_event)` to apply the cutoff.

Track decrypted messages with no usable timestamp and emit a `message_timestamp_unavailable` data-gap count. Do not classify these messages as waiting, replied, or empty.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the Step 2 command. Expected: all Chat collector tests pass.

- [ ] **Step 5: Commit decrypt-first processing**

```bash
git add twitter-digest/scripts/chat_x_digest.py twitter-digest/tests/test_chat_x_digest.py
git commit -m "fix(twitter-digest): decrypt X Chat before time filtering"
```

### Task 3: Honest Conversation-List Completeness

**Files:**
- Modify: `twitter-digest/tests/test_chat_x_digest.py`
- Modify: `twitter-digest/scripts/chat_x_digest.py:180-207,372-590`
- Modify: `twitter-digest/SKILL.md`

**Interfaces:**
- Produces: `collect_conversations(...) -> tuple[list[dict], dict[str, dict], bool, dict[str, Any]]` where metadata contains `complete`, `next_token`, and `missing_id_count`.
- Produces: final `dm_scan_complete` equal to list completeness AND event completeness AND no truncated conversations.

- [ ] **Step 1: Write failing list-boundary tests**

Add a test returning exactly the requested maximum plus `meta.next_token="more"`. Assert the metadata is:

```python
{"complete": False, "next_token": "more", "missing_id_count": 0}
```

Add a response containing one valid conversation and one conversation without `id`; assert the missing item is not fetched and `missing_id_count == 1` makes the scan incomplete.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
python3 -m unittest twitter-digest/tests/test_chat_x_digest.py -v
```

Expected: tuple-shape assertions fail because list completeness is not returned.

- [ ] **Step 3: Implement completeness propagation**

Return conversation metadata from `collect_conversations`. Preserve the remaining `next_token` when the configured maximum stops pagination. Count missing conversation IDs rather than silently skipping them.

Initialize `scan_complete` from list metadata. Preserve the existing event-budget, page-cap, and consecutive-old stop reasons. Ensure incomplete list pagination cannot be overwritten by later event-loop state.

Update the skill rule to state that a conversation-list pagination boundary is also a safe-scan boundary and uses the existing friendly sentence `X Chat 已检查最近的 N 个会话。`.

- [ ] **Step 4: Run Chat and digest-context tests and verify GREEN**

```bash
python3 -m unittest twitter-digest/tests/test_chat_x_digest.py twitter-digest/tests/test_digest_context_chat.py -v
```

Expected: all tests pass and incomplete scans remain informational rather than false empty-inbox claims.

- [ ] **Step 5: Commit completeness accounting**

```bash
git add twitter-digest/scripts/chat_x_digest.py twitter-digest/tests/test_chat_x_digest.py twitter-digest/SKILL.md
git commit -m "fix(twitter-digest): report incomplete X Chat list scans"
```

### Task 4: Release and Full Verification

**Files:**
- Modify: `twitter-digest/install.sh`
- Modify: `twitter-digest/README.md`
- Modify: `twitter-digest/tests/test_security_contract.py`

**Interfaces:**
- Produces: installer tag `v1.5.14-beta.12` for Codex and Claude installation commands.

- [ ] **Step 1: Write the failing release-tag test**

Change `test_security_contract.py` to expect `v1.5.14-beta.12` in `install.sh` and `README.md`.

- [ ] **Step 2: Run the release test and verify RED**

```bash
python3 -m unittest twitter-digest/tests/test_security_contract.py -v
```

Expected: failures still show `v1.5.14-beta.11`.

- [ ] **Step 3: Update installer documentation**

Replace the twitter-digest release tag with `v1.5.14-beta.12` in `install.sh` and both README installation commands. Do not alter permission opt-ins or introduce write scopes.

- [ ] **Step 4: Run complete verification**

```bash
python3 -m unittest discover -s twitter-digest/tests -p 'test_*.py' -v
python3 twitter-digest/scripts/install.py --help
sh -n twitter-digest/install.sh twitter-digest/uninstall.sh
git diff --check
```

Expected: all unit tests pass, both scripts parse, installer help exits 0, and diff check produces no errors.

- [ ] **Step 5: Inspect the scoped diff and commit**

```bash
git diff --stat HEAD -- twitter-digest docs/superpowers
git status --short
git add twitter-digest/install.sh twitter-digest/README.md twitter-digest/tests/test_security_contract.py
git commit -m "release(twitter-digest): prepare v1.5.14-beta.12"
```

Confirm the unrelated `twitter-mcp` modifications remain unstaged and unchanged.
