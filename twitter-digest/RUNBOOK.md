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
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api
python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py --configure-api
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
3. If no usable token exists, it opens API configuration in a real Terminal when necessary, then exits the current command with `api_configuration_required`.
4. After the user finishes API configuration, run the digest command again.
5. It runs `api_x_digest.py` only after a usable API token exists.
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

## DM / X Chat

API DM coverage is incomplete. If API DM returns zero or fails, report a data gap. Do not claim there are no DMs from API results alone.

Non-API DM collection is not part of this skill.

## Install Prerequisites

- `git`
- `python3` 3.9+

Only `git` and Python 3.9+ are required.

## Troubleshooting

- Missing config: API configuration is required; run `run_daily_digest.py --configure-api`.
- Token refresh failure: rerun configuration.
- 401/403/rate limit/API tier issues: report the API data gap.
- Non-API source request: explain that this skill only supports API collection.
