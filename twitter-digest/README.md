# X/Twitter Digest

Skill for generating a Chinese daily digest from a user's own X/Twitter account. This version is API-only.

## Quick Install

Codex:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.13-beta.2/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_CLIENT=codex sh
```

Claude Code:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.13-beta.2/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_CLIENT=claude TWITTER_DIGEST_ALLOW_CLAUDE_COMMANDS=1 TWITTER_DIGEST_ALLOW_CLAUDE_STATE_READ=1 sh
```

From a checkout:

```bash
python3 twitter-digest/scripts/install.py
```

The installer opens a real macOS Terminal when launched from Codex, Claude Code, or another non-interactive agent. Set `TWITTER_DIGEST_OPEN_TERMINAL=0` only when intentionally running inside an interactive Terminal or CI.

Install targets:

```text
Codex: ~/.codex/skills/twitter-digest
Claude Code: ~/.claude/skills/twitter-digest
```

The installer requires Python 3.9+. Reinstalling is the upgrade path: existing code is replaced and the installed `.state` directory is preserved.

## Run

Use the installed command:

```text
Claude Code: python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py
Codex:       python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py
```

`run_daily_digest.py` uses API. A valid API configuration is required before a digest can be generated. If API credentials are missing or expired, the wrapper starts API configuration and continues API collection only after configuration succeeds.

## Required API Configuration

From chat or Terminal:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api
python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py --configure-api
```

The setup flow is required for first use. It uses OAuth2 PKCE, asks for the X Developer App Client ID, opens the X authorization page, waits for the local callback, and saves a user-context access token plus refresh token.

Scopes:

```text
tweet.read users.read offline.access dm.read
```

If the user already has an OAuth2 user access token:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api-token
python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py --configure-api-token
```

Verify:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/configure_api.py --verify
python3 ~/.codex/skills/twitter-digest/scripts/configure_api.py --verify
```

Clear:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/configure_api.py --clear
python3 ~/.codex/skills/twitter-digest/scripts/configure_api.py --clear
```

## Data Source

Only one collector is supported:

```bash
python3 twitter-digest/scripts/api_x_digest.py
```

API source collects:

- Home timeline when the token has user-context access.
- Mentions and recent search results.
- Own profile activity.
- Optional keyword searches.

DM / X Chat limitation:

- API DM results are incomplete for many accounts.
- Do not conclude "no DMs" from zero API DM events.
- Non-API DM collection is not part of this skill.

All final facts are filtered to the user's current local 24-hour window.

## Outputs

```text
<installed-skill>/.state/run/digest-context.md
<installed-skill>/.state/run/digest-context.json
<installed-skill>/.state/run/digest-context-timeline.md
<installed-skill>/.state/run/digest-context-mentions.md
<installed-skill>/.state/run/digest-context-dm.md
<installed-skill>/.state/run/digest-input.md
<installed-skill>/.state/run/digest-input.json
```

Use `digest-context.md` as the normal AI input. Use `digest-input.*` only for debugging.

## Uninstall

Safe uninstall moves the installed skill to `.backups/` and preserves `.state`:

```bash
~/.codex/skills/twitter-digest/uninstall.sh --client codex
~/.claude/skills/twitter-digest/uninstall.sh --client claude
```

To permanently remove the installed skill, `.state`, and matching `.backups` entries:

```bash
~/.codex/skills/twitter-digest/uninstall.sh --client codex --purge-state
~/.claude/skills/twitter-digest/uninstall.sh --client claude --purge-state
```

## Details

See:

- `SKILL.md`
- `RUNBOOK.md`
- `DATA_COLLECTION.md`
- `FUNCTION_RULES_FLOW.md`
- `references/x-twitter-digest.md`
