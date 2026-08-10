# Twitter Digest Rate-Limit Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release `v1.5.14-beta.11` with privacy-safe endpoint-specific X Chat 429 messages, immediate configuration stop on 429, and per-endpoint request counts.

**Architecture:** Add a small structured diagnostic contract to the shared collector utilities, emit it from both X Chat request helpers, and translate it at the wrapper boundary. Keep route normalization and counting in the request layer so every HTTP attempt is measured while user-facing code sees only allowlisted endpoint categories.

**Tech Stack:** Python 3.10+, `unittest`, `urllib.request`, POSIX shell installer.

## Global Constraints

- Never expose a concrete conversation ID, user ID, token, raw response body, or X Chat passcode.
- HTTP 429 stops immediately in normal Chat collection and Chat configuration.
- Keep the `beta.10` event budget, reserve, pagination cap, old-conversation stop, public-key cache, and read-only restrictions unchanged.
- Keep legacy plain-text collector error support.
- Release tag is exactly `v1.5.14-beta.11`.

---

### Task 1: Structured diagnostic contract and wrapper wording

**Files:**
- Modify: `twitter-digest/scripts/collector_commands.py`
- Modify: `twitter-digest/scripts/run_daily_digest.py`
- Test: `twitter-digest/tests/test_collector_commands.py`
- Test: `twitter-digest/tests/test_security_contract.py`

**Interfaces:**
- Produces: `structured_api_error(source, endpoint, status, retry_after_seconds=None) -> str`
- Produces: `parse_structured_api_error(text) -> dict[str, object] | None`
- Produces: `friendly_chat_collection_error(summary) -> str`

- [ ] **Step 1: Write failing tests** for parsing an event-route 429 marker, preserving retry delay, removing a concrete conversation ID, mapping three endpoint categories to Chinese, and falling back for legacy errors.
- [ ] **Step 2: Run focused tests** with `python3 -m unittest twitter-digest/tests/test_collector_commands.py twitter-digest/tests/test_security_contract.py` and confirm failures are caused by missing interfaces.
- [ ] **Step 3: Implement the minimal allowlisted JSON marker parser/serializer** and make `summarize_collector_error()` prefer it over keyword extraction.
- [ ] **Step 4: Implement friendly wrapper translation** with rounded-up minutes and no endpoint identifiers in user text.
- [ ] **Step 5: Re-run focused tests** and confirm they pass.

### Task 2: Normal X Chat route normalization and request counts

**Files:**
- Modify: `twitter-digest/scripts/chat_x_digest.py`
- Test: `twitter-digest/tests/test_chat_x_digest.py`

**Interfaces:**
- Consumes: `structured_api_error(...)` from Task 1.
- Produces: `endpoint_category(path) -> str`
- Produces: `HTTP_REQUEST_COUNTS: dict[str, int]`
- Produces payload field `dm_api_request_counts`.

- [ ] **Step 1: Write failing tests** proving conversation IDs normalize to `conversation_events`, user IDs normalize to `public_keys`, each `urlopen` attempt increments the correct counter, and a 429 emits a structured marker without IDs.
- [ ] **Step 2: Run `python3 -m unittest twitter-digest/tests/test_chat_x_digest.py`** and confirm the new tests fail for the intended missing behavior.
- [ ] **Step 3: Implement route categorization and attempt counting** immediately before each `urlopen` call.
- [ ] **Step 4: Replace raw 429 text with the structured marker** while retaining `RateLimitError` and immediate stop.
- [ ] **Step 5: Add a zero-filled `dm_api_request_counts` object to successful payloads** and retain `dm_event_request_count` as the logical budget counter.
- [ ] **Step 6: Re-run focused tests** and confirm they pass.

### Task 3: Configuration 429 behavior

**Files:**
- Modify: `twitter-digest/scripts/configure_chat.py`
- Test: `twitter-digest/tests/test_configure_chat.py`

**Interfaces:**
- Consumes: `structured_api_error(...)` from Task 1.
- Produces: configuration `api_get(token, path)` that stops after one 429 and keeps bounded retries for transient non-429 responses.

- [ ] **Step 1: Write failing tests** asserting one `urlopen` call for 429, structured `public_keys` diagnostics without user IDs, and a second attempt after a transient 503.
- [ ] **Step 2: Run `python3 -m unittest twitter-digest/tests/test_configure_chat.py`** and confirm the 429 behavior test fails.
- [ ] **Step 3: Implement immediate 429 termination** using the shared structured marker while leaving non-429 retry behavior unchanged.
- [ ] **Step 4: Re-run focused tests** and confirm they pass.

### Task 4: Skill contract, reporting metadata, and release version

**Files:**
- Modify: `twitter-digest/SKILL.md`
- Modify: `twitter-digest/agents/openai.yaml`
- Modify: `twitter-digest/README.md`
- Modify: `twitter-digest/install.sh`
- Modify: `twitter-digest/scripts/digest_context.py`
- Modify: `twitter-digest/scripts/inspect_digest.py`
- Test: `twitter-digest/tests/test_digest_context_chat.py`
- Test: `twitter-digest/tests/test_security_contract.py`

**Interfaces:**
- Consumes payload field `dm_api_request_counts` from Task 2.
- Produces internal context field `dms.api_request_counts` and inspection output `chat.scan.api_request_counts`.

- [ ] **Step 1: Write failing contract/context tests** for internal request counts, friendly endpoint-specific rate-limit wording, and `beta.11` installer references.
- [ ] **Step 2: Run focused tests** and verify the new assertions fail.
- [ ] **Step 3: Carry request counts into context and inspection output** without adding them to normal digest prose.
- [ ] **Step 4: Update Skill instructions and agent prompt** to require friendly messages and prohibit exposing raw paths/IDs.
- [ ] **Step 5: Update README and installer tag** to `v1.5.14-beta.11`.
- [ ] **Step 6: Re-run focused tests** and confirm they pass.

### Task 5: Verification, installation, and release

**Files:**
- Verify all modified files.

**Interfaces:**
- Produces: published Git tag `v1.5.14-beta.11` and working Codex/Claude installation commands.

- [ ] **Step 1: Run all tests** with `python3 -m unittest discover -s twitter-digest/tests -p 'test_*.py'`.
- [ ] **Step 2: Run static checks** with `python3 -m compileall -q twitter-digest/scripts twitter-digest/tests`, `git diff --check`, and `sh -n twitter-digest/install.sh`.
- [ ] **Step 3: Run Skill validation** with `quick_validate.py` and PyYAML available on `PYTHONPATH`.
- [ ] **Step 4: Run installer dry-run** and inspect the installed files for `beta.11`, endpoint diagnostics, and safe-scan constants.
- [ ] **Step 5: Commit implementation, fast-forward the release branch, tag, and push** without touching unrelated `twitter-mcp` changes.
- [ ] **Step 6: Install from the remote tag into Codex and Claude** and verify both installed copies contain `beta.11` and the new tests/markers.
