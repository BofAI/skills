# Twitter Digest Runbook

`twitter-digest` is API-only.

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

1. `run_daily_digest.py` loads saved `.state/api_config.json`.
2. If an OAuth refresh token exists, it refreshes the access token when needed.
3. If API or X Chat state is missing or invalid, it opens one configuration wizard in a real Terminal, then exits the current command with `configuration_required`.
4. After the user finishes API configuration, run the digest command again.
5. It requires saved X Chat keys, then runs `api_x_digest.py` and `chat_x_digest.py`.
6. It builds current-run context files with `digest_context.py`.

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

X Chat is mandatory. Configure API and Chat together with `run_daily_digest.py --configure`. The same Terminal flow collects Client ID, Client Secret, and the user's Chat passcode, saves an owner-only local key blob, and never saves the passcode. Existing valid steps are skipped. Collection or decryption failure stops the digest.

Browser/cookie DM collection is not part of this skill.

## Install Prerequisites

- `git`
- `python3` 3.10+

Chat configuration creates a private runtime under `.state/chat/runtime`.

## Troubleshooting

- Missing config: unified API and X Chat configuration is required; run `run_daily_digest.py --configure`.
- Token refresh failure: rerun configuration.
- 401/403/rate limit/API tier issues: report the API data gap.
- Non-API source request: explain that this skill only supports API collection.
