# Twitter Digest Runbook

`twitter-digest` is API-only.

## Install

Codex:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.14-beta.14/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_CLIENT=codex sh
```

Claude Code:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.14-beta.14/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_CLIENT=claude TWITTER_DIGEST_ALLOW_CLAUDE_COMMANDS=1 TWITTER_DIGEST_ALLOW_CLAUDE_STATE_READ=1 sh
```

Standard installs immediately run the unified X API and X Chat configuration check. Existing valid state is reused. Set `TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL=0` to install without configuration; custom `--skills-dir` installs and dry runs also skip it.

## Entry Points

Normal digest:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py
python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py
```

Configure API:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure
python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py --configure
```

Verify API:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/configure_api.py --verify
python3 ~/.codex/skills/twitter-digest/scripts/configure_api.py --verify
```

The wrapper uses API directly.

## Runtime Flow

1. Standard installation checks X API and X Chat configuration before the first digest; the runtime wrapper repeats this check as a fallback.
2. `run_daily_digest.py` loads saved `.state/api_config.json`.
3. If an OAuth refresh token exists, it refreshes the access token when needed.
4. If API or X Chat state is missing or invalid, it opens one configuration wizard in a real Terminal, then exits the current command with `configuration_required`.
5. After the user finishes API configuration, run the digest command again.
6. It requires saved X Chat keys, then runs `api_x_digest.py` and `chat_x_digest.py`.
7. It builds current-run context files with `digest_context.py`.

OAuth authorization may open the X authorization page, but that is not data collection.

## Upgrade Behavior

Reinstalling is upgrading:

- Existing installed skill code is moved to `.backups/`.
- Backup `SKILL.md` files are disabled so agents do not load old versions.
- The active installed `.state` directory is restored into the new install.

Safe uninstall preserves `.state`; `--purge-state` removes active state and matching backups.

## API Data

The API collector writes the same current-run output shape on every run:

- `digest-input.json`
- `digest-input.md`
- `digest-context.md`
- `digest-context.json`
- `digest-context-timeline.md`
- `digest-context-mentions.md`
- `digest-context-dm.md`

Use the agent file Read tool to read `digest-context.md`. Do not inspect private context with shell commands during normal summarization.

## Time Window

Final digest facts use the user's local timezone and the window:

```text
[now - 24 hours, now]
```

Items outside the window must not appear as current action items. Items without parseable timestamps are excluded from final facts and reported as data gaps.

## Mentions

Mention sources:

- Direct mention/notification data when available.
- Recent search for the authenticated handle.

Do not treat stale mentions as current. Do not mark an already-replied mention as pending. If reply state cannot be verified from the current API run, label it `回复状态未确认`.

## X Chat

X Chat is mandatory. Configure API and Chat together with `run_daily_digest.py --configure`. If X Chat has no passcode-backed key, the Terminal explains how to set a passcode in X Messages and opens that page only after the user confirms. With an existing passcode, unlock retries up to three times locally without refetching public keys or rebuilding the runtime. The flow saves an owner-only local key blob and never saves the passcode. Existing valid steps are skipped. Collection or decryption failure stops the digest.

Normal runs use `--chat-scan recent`: at most 10 conversations, 10 event requests, and one event page per conversation. `--chat-scan more` is only for an explicit request to see more and raises those caps to 50, 20, and three. A 168-hour Chat window automatically selects the larger profile.

After decryption, the first conversation whose newest reliable message predates the window stops the scan. The conversation list itself uses at most five requests and stops on three consecutive empty pages, a repeated pagination token, or `has_more` without a token.

Known 429 retry intervals are cached in `.state/chat/rate_limits.json` using only a sanitized endpoint category and expiry. Repeated runs during that cooldown return a friendly message without calling X again.

Browser/cookie DM collection is not part of this skill.

## Install Prerequisites

- `git`
- `python3` 3.10+

Chat configuration creates a private runtime under `.state/chat/runtime`.

## Troubleshooting

- Missing config: unified API and X Chat configuration is required; run `run_daily_digest.py --configure`.
- Token refresh failure: rerun configuration.
- 401/403/API tier issues: report the API data gap. For X Chat 429, keep the friendly endpoint-level message and wait for the cached cooldown instead of retrying repeatedly.
- Non-API source request: explain that this skill only supports API collection.
