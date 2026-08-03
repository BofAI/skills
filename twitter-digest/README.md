# X/Twitter Digest

Skill for generating a Chinese daily digest from a user's own X/Twitter account. This version is API-only.

## Quick Install

Codex:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.14-beta.1/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_CLIENT=codex sh
```

Claude Code:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.14-beta.1/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_CLIENT=claude TWITTER_DIGEST_ALLOW_CLAUDE_COMMANDS=1 TWITTER_DIGEST_ALLOW_CLAUDE_STATE_READ=1 sh
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

The installer requires Python 3.10+. Reinstalling is the upgrade path: existing code is replaced and the installed `.state` directory, including X Chat keys/runtime, is preserved.

## Run

Use the installed command:

```text
Claude Code: python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py
Codex:       python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py
```

`run_daily_digest.py` uses API. A valid API configuration is required before a digest can be generated. If API credentials are missing or expired, the wrapper opens the API configuration flow. After configuration succeeds, run the digest command again.

## Required API Configuration

From chat or Terminal:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure
python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py --configure
```

The setup flow is required for first use. It opens one Terminal window, asks for Client ID, Client Secret, and X Chat passcode in sequence, opens the X authorization page, and saves the API and Chat state. Existing valid configuration is skipped during reinstall or upgrade.

Scopes:

```text
tweet.read users.read offline.access dm.read dm.write
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

## Required X Chat Configuration

After API OAuth is configured:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure
python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py --configure
```

The Terminal flow installs Chat XDK into the skill's private state directory, asks for the X Chat passcode, unlocks the registered identity keys, and saves an owner-only local key blob. The passcode is never saved. The blob is unencrypted private identity material required for unattended runs; protect `.state` and use uninstall `--purge-state` to remove active and backed-up copies.

## Data Source

One API source uses two required collectors:

```bash
python3 twitter-digest/scripts/api_x_digest.py
python3 twitter-digest/scripts/chat_x_digest.py
```

API source collects:

- Home timeline when the token has user-context access.
- Mentions and recent search results.
- Own profile activity.
- Optional keyword searches.

X Chat is required. A Chat collection or decryption failure stops the digest. Browser/cookie DM collection is not part of this skill.

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
