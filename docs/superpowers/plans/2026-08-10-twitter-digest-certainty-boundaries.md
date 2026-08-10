# Twitter Digest Certainty Boundaries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the unreliable X Chat request flag end to end and prevent adjacent weak evidence from becoming definite reply, action, or authentication states.

**Architecture:** Keep the existing collector → current-run JSON → normalized context pipeline. Tighten certainty at the source when new data is produced, retain one compatibility filter for legacy run files, and require direct evidence before assigning actionable states.

**Tech Stack:** Python 3.10+, `unittest`, Chat XDK runtime, Markdown skill documentation, POSIX installer.

## Global Constraints

- The skill remains API-only and requires X Chat.
- Do not change OAuth scopes, passcode storage, Chat scan limits, rate-limit cooldowns, or installer commands.
- Never add posting, replying, liking, following, accepting requests, or DM sending.
- New Chat payloads must omit `dm_has_message_requests`; legacy payloads must remain safe to render.
- Every behavior change follows RED → GREEN and ends with focused plus complete verification.

---

### Task 1: Remove the X message-request signal from new collection

**Files:**
- Modify: `twitter-digest/tests/test_chat_x_digest.py`
- Modify: `twitter-digest/scripts/chat_x_digest.py`

**Interfaces:**
- Consumes: `collect_conversations(token: str, maximum: int, max_requests: int = 5, max_empty_pages: int = 3)`.
- Produces: `tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]`; new Chat JSON has no `dm_has_message_requests`.

- [ ] **Step 1: Write failing collector tests**

Rename the pagination test to `test_collect_conversations_follows_pagination_and_ignores_request_flag`, unpack three values, and assert the pagination contract. Rename the main-output test to `test_message_request_meta_is_not_written` and require the field to be absent:

```python
conversations, users, scan = chat_x_digest.collect_conversations("token", 50)
self.assertNotIn("dm_has_message_requests", payload)
self.assertEqual(payload["todo_items"], [])
```

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
python3 -m unittest twitter-digest.tests.test_chat_x_digest.ChatCollectorTests.test_collect_conversations_follows_pagination_and_ignores_request_flag twitter-digest.tests.test_chat_x_digest.ChatCollectorTests.test_message_request_meta_is_not_written
```

Expected: failure from the four-value return and the still-present `dm_has_message_requests` field.

- [ ] **Step 3: Implement the source removal**

Remove `has_message_requests`, the `meta.get("has_message_requests")` read, and the boolean return from `collect_conversations`. Update `main()` to unpack three values and remove this payload entry:

```python
"dm_has_message_requests": has_message_requests,
```

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
python3 -m unittest twitter-digest/tests/test_chat_x_digest.py
```

Expected: all Chat collector tests pass.

- [ ] **Step 5: Commit**

```bash
git add twitter-digest/scripts/chat_x_digest.py twitter-digest/tests/test_chat_x_digest.py
git commit -m "fix(twitter-digest): drop unreliable chat request flag"
```

### Task 2: Require direct evidence for public reply state

**Files:**
- Modify: `twitter-digest/tests/test_digest_context_public.py`
- Modify: `twitter-digest/scripts/digest_context.py`

**Interfaces:**
- Consumes: normalized mention and own-post dictionaries with `id`, `raw_time`, and `referenced_tweets`.
- Produces: `find_reply_evidence(mention: dict[str, Any], own_items: list[dict[str, Any]]) -> str` only for a later own post whose `replied_to` reference equals the mention ID.

- [ ] **Step 1: Write failing certainty tests**

Add three tests with literal fixtures:

```python
def test_later_post_in_same_conversation_is_not_reply_evidence(self) -> None:
    mention = {
        "kind": "mentions_notifications", "id": "200", "conversation_id": "thread",
        "author_username": "alice", "raw_time": "2026-08-06T02:00:00Z",
        "referenced_tweets": [],
    }
    own = {
        "kind": "own_profile", "id": "201", "conversation_id": "thread",
        "author_username": "owner", "raw_time": "2026-08-06T03:00:00Z",
        "referenced_tweets": [],
    }
    result = digest_context.annotate_public_reply_states([mention, own], "owner")[0]
    self.assertNotEqual(result.get("reply_state"), "already_replied")

def test_later_post_mentioning_same_author_is_not_reply_evidence(self) -> None:
    mention = {
        "kind": "mentions_search", "id": "200", "author_username": "alice",
        "raw_time": "2026-08-06T02:00:00Z", "referenced_tweets": [],
    }
    own = {
        "kind": "own_profile", "id": "201", "author_username": "owner",
        "raw_time": "2026-08-06T03:00:00Z", "text_excerpt": "hello @alice",
        "referenced_tweets": [],
    }
    result = digest_context.annotate_public_reply_states([mention, own], "owner")[0]
    self.assertNotEqual(result.get("reply_state"), "already_replied")

def test_direct_later_reply_reference_is_reply_evidence(self) -> None:
    mention = {
        "kind": "mentions_notifications", "id": "200", "author_username": "alice",
        "raw_time": "2026-08-06T02:00:00Z", "referenced_tweets": [],
    }
    own = {
        "kind": "own_profile", "id": "201", "author_username": "owner",
        "raw_time": "2026-08-06T03:00:00Z",
        "referenced_tweets": [{"id": "200", "type": "replied_to"}],
    }
    result = digest_context.annotate_public_reply_states([mention, own], "owner")[0]
    self.assertEqual(result["reply_state"], "already_replied")
```

The first two assert the mention is not `already_replied`; the third uses an own post containing `{"id": "200", "type": "replied_to"}` and asserts `already_replied`.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
python3 -m unittest twitter-digest/tests/test_digest_context_public.py
```

Expected: the same-conversation and same-author cases fail because current heuristics return reply evidence.

- [ ] **Step 3: Implement direct-reference-only evidence**

Replace broad `referenced_ids` matching and remove the conversation/author fallbacks. Use:

```python
def replied_to_ids(item: dict[str, Any]) -> set[str]:
    refs = item.get("referenced_tweets") if isinstance(item.get("referenced_tweets"), list) else []
    return {
        compact_text(ref.get("id"))
        for ref in refs
        if isinstance(ref, dict) and ref.get("type") == "replied_to" and ref.get("id")
    }
```

Require the own post to be later when both timestamps are known, then return evidence only when `mention_id in replied_to_ids(own)`.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
python3 -m unittest twitter-digest/tests/test_digest_context_public.py
```

Expected: all public-context tests pass.

- [ ] **Step 5: Commit**

```bash
git add twitter-digest/scripts/digest_context.py twitter-digest/tests/test_digest_context_public.py
git commit -m "fix(twitter-digest): require direct reply evidence"
```

### Task 3: Make uncertain X Chat threads non-actionable

**Files:**
- Modify: `twitter-digest/tests/test_digest_context_chat.py`
- Modify: `twitter-digest/tests/test_chat_x_digest.py`
- Modify: `twitter-digest/scripts/digest_context.py`
- Modify: `twitter-digest/scripts/digest_io.py`
- Modify: `twitter-digest/scripts/chat_x_digest.py`

**Interfaces:**
- Consumes: explicit `reply_state` or legacy `replied: bool | None`.
- Produces: `normalize_dm_reply_state(thread: dict[str, Any]) -> str` returning `last_from_me`, `waiting_reply`, or `unknown`; unavailable threads contain no UI action.

- [ ] **Step 1: Write failing DM-state tests**

Add context tests for missing and legacy state:

```python
self.assertEqual(digest_context.normalize_dm_reply_state({}), "unknown")
self.assertEqual(digest_context.normalize_dm_reply_state({"replied": None}), "unknown")
self.assertEqual(digest_context.normalize_dm_reply_state({"replied": True}), "last_from_me")
self.assertEqual(digest_context.normalize_dm_reply_state({"replied": False}), "waiting_reply")
```

Update the unavailable-thread test to assert `requires_user_ui` and `user_action` are absent.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
python3 -m unittest twitter-digest/tests/test_digest_context_chat.py twitter-digest.tests.test_chat_x_digest.ChatCollectorTests.test_unavailable_thread_never_claims_reply_state
```

Expected: missing helper and current UI-action fields fail.

- [ ] **Step 3: Implement explicit state normalization**

Add:

```python
def normalize_dm_reply_state(thread: dict[str, Any]) -> str:
    explicit = str(thread.get("reply_state") or "")
    if explicit in {"last_from_me", "waiting_reply", "unknown"}:
        return explicit
    replied = thread.get("replied")
    if isinstance(replied, bool):
        return "last_from_me" if replied else "waiting_reply"
    return "unknown"
```

Use it when assessing threads, building facts, and rendering raw Markdown in both `digest_context.py` and `digest_io.py`. Remove `requires_user_ui` and `user_action` from `unavailable_thread` output. Keep unknown senders in the existing historical sentence only.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
python3 -m unittest twitter-digest/tests/test_digest_context_chat.py twitter-digest/tests/test_chat_x_digest.py
```

Expected: all Chat context and collector tests pass.

- [ ] **Step 5: Commit**

```bash
git add twitter-digest/scripts/digest_context.py twitter-digest/scripts/digest_io.py twitter-digest/scripts/chat_x_digest.py twitter-digest/tests/test_digest_context_chat.py twitter-digest/tests/test_chat_x_digest.py
git commit -m "fix(twitter-digest): keep uncertain chats non-actionable"
```

### Task 4: Remove blind X Chat authentication retry

**Files:**
- Modify: `twitter-digest/tests/test_security_contract.py`
- Modify: `twitter-digest/scripts/run_daily_digest.py`

**Interfaces:**
- Consumes: a failed Chat subprocess and `summarize_collector_error` output.
- Produces: one `ChatCollectionError` and final wrapper failure with the exact friendly text `X Chat 授权已失效。请运行统一配置后重新生成日报。` for authentication failures.

- [ ] **Step 1: Rewrite the 401 test for desired behavior**

```python
with self.assertRaises(run_daily_digest.ChatCollectionError) as raised:
    run_daily_digest.run_chat_command(["chat"], {})
self.assertEqual(run.call_count, 1)
self.assertEqual(str(raised.exception), "X Chat 授权已失效。请运行统一配置后重新生成日报。")
self.assertNotIn("/chat/conversations", str(raised.exception))
self.assertEqual(
    run_daily_digest.format_chat_collection_failure(str(raised.exception)),
    "X Chat 授权已失效。请运行统一配置后重新生成日报。",
)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python3 -m unittest twitter-digest.tests.test_security_contract.SecurityContractTests.test_x_chat_401_is_retried_only_once
```

Expected: current implementation executes the subprocess twice and does not raise the friendly error.

- [ ] **Step 3: Implement single-attempt authentication handling**

Define `CHAT_AUTH_FAILURE = "X Chat 授权已失效。请运行统一配置后重新生成日报。"`. Make `format_chat_collection_failure` return this value unchanged. Replace the loop in `run_chat_command` with one subprocess execution. On failure:

```python
if api_auth_needs_reconfigure(detail):
    raise ChatCollectionError(CHAT_AUTH_FAILURE) from exc
raise ChatCollectionError(detail or f"chat collector exited with code {exc.returncode}") from exc
```

- [ ] **Step 4: Run security tests and verify GREEN**

Run:

```bash
python3 -m unittest twitter-digest/tests/test_security_contract.py
```

Expected: all security-contract tests pass and non-auth failures still run once.

- [ ] **Step 5: Commit**

```bash
git add twitter-digest/scripts/run_daily_digest.py twitter-digest/tests/test_security_contract.py
git commit -m "fix(twitter-digest): stop blind chat auth retry"
```

### Task 5: Align guidance, legacy compatibility, and installed behavior

**Files:**
- Modify: `twitter-digest/SKILL.md`
- Modify: `twitter-digest/DATA_COLLECTION.md`
- Modify: `docs/superpowers/specs/2026-08-10-twitter-digest-xchat-field-completeness-design.md`
- Verify: `twitter-digest/tests/test_digest_context_chat.py`

**Interfaces:**
- Consumes: old run files containing `dm_has_message_requests` and `message_request_pending`.
- Produces: no request count, todo, action, or rendered text; current documentation contains no live guidance based on that flag.

- [ ] **Step 1: Confirm the legacy compatibility contract before documentation edits**

Run:

```bash
python3 -m unittest twitter-digest.tests.test_digest_context_chat.DigestContextChatTests.test_unverified_message_request_signal_is_not_shown_as_current_todo
```

Expected: PASS. The fixture contains both the legacy field and legacy todo and must remain unchanged while new-payload production is removed.

- [ ] **Step 2: Update documentation**

Remove the active diagnostic rule for `has_message_requests`. State only that legacy occurrences are ignored. Update the earlier field-completeness design paragraph that called the flag a true-only action signal.

- [ ] **Step 3: Run the complete verification suite**

Run:

```bash
python3 -m unittest discover -s twitter-digest/tests -p 'test_*.py'
uv run --with pyyaml python /Users/bobo/.codex/skills/.system/skill-creator/scripts/quick_validate.py twitter-digest
git diff --check
```

Expected: zero test failures, `Skill is valid!`, and no whitespace errors.

- [ ] **Step 4: Verify a real saved legacy capture**

Build context from `~/.codex/skills/twitter-digest/.state/run/digest-input.json` into a new `mktemp -d` directory. Assert that an old `dm_has_message_requests=true` is tolerated but the generated context contains no `message_requests`, `message_request_pending`, `消息请求`, or `X → 消息 → 请求`.

- [ ] **Step 5: Commit documentation and compatibility changes**

```bash
git add twitter-digest/SKILL.md twitter-digest/DATA_COLLECTION.md docs/superpowers/specs/2026-08-10-twitter-digest-xchat-field-completeness-design.md twitter-digest/tests/test_digest_context_chat.py
git commit -m "docs(twitter-digest): align certainty rules"
```

- [ ] **Step 6: Reinstall and smoke-test both clients**

Run `twitter-digest/install.sh` from the committed branch with `TWITTER_DIGEST_OPEN_TERMINAL=0`, local `TWITTER_DIGEST_INSTALL_REPO`, and `TWITTER_DIGEST_INSTALL_CLIENT=codex`, then repeat for `claude` with the existing two Claude permission flags. Compare installed source files with the worktree and rebuild context from the preserved Codex run file.
