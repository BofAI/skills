# X/Twitter Digest

Skill for generating a Chinese daily digest from a user's own X/Twitter account through API collection when configured, otherwise through a saved local browser session.

## Quick Install

From a fresh checkout:

```bash
git clone git@github.com:BofAI/skills.git
cd skills
python3 twitter-digest/scripts/install.py
```

To ask Codex to install this skill for itself, paste this into Codex:

```bash
TMPDIR="$(mktemp -d)" && git clone --depth 1 --branch v1.5.11-beta.12 https://github.com/BofAI/skills.git "$TMPDIR/skills" && python3 "$TMPDIR/skills/twitter-digest/scripts/install.py" --client codex
```

Or use the natural-language prompt:

```text
请帮我安装这个 Codex skill：

git clone git@github.com:BofAI/skills.git bofai-skills \
  && cd bofai-skills \
  && python3 twitter-digest/scripts/install.py --client codex

安装后请确认 ~/.codex/skills/twitter-digest 存在。首次运行日报时，如果弹出浏览器，请让我登录 X。
```

To ask Claude Code to install this skill for itself, paste this into Claude Code:

```bash
TMPDIR="$(mktemp -d)" && git clone --depth 1 --branch v1.5.11-beta.12 https://github.com/BofAI/skills.git "$TMPDIR/skills" && python3 "$TMPDIR/skills/twitter-digest/scripts/install.py" --client claude --allow-claude-commands --allow-claude-state-read
```

Or use the natural-language prompt:

```text
请帮我安装这个 Claude Code skill：

git clone git@github.com:BofAI/skills.git bofai-skills \
  && cd bofai-skills \
  && python3 twitter-digest/scripts/install.py --client claude --allow-claude-commands --allow-claude-state-read

安装后请确认 ~/.claude/skills/twitter-digest 存在。首次运行日报时，如果 Claude Code 弹出 Bash 授权，批准 `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py`；如果弹出浏览器，请让我登录 X。
```

The installer chooses the target by client:

```text
Codex: ~/.codex/skills/twitter-digest
Claude Code: ~/.claude/skills/twitter-digest
```

It also checks for Python 3.10+ and a supported Chromium browser: Google Chrome, Chromium, Microsoft Edge, or Brave.
Reinstalling preserves the existing installed `.state` directory, including saved API and browser-session settings. The installer still excludes `.state` from the development checkout.
After installation, configure and run the installed copy. If a script is accidentally started from a temporary clone while an installed copy exists, it automatically re-runs the installed copy so state is saved under `~/.claude/skills/twitter-digest/.state` or `~/.codex/skills/twitter-digest/.state`.

Use one stable installed command form for normal runs. This prevents repeated Claude Code Bash permission prompts across different projects:

```text
Claude Code: python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py
Codex:       python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py
```

Claude Code cannot let a skill silently grant itself Bash permission or file access outside the project. Either approve the first visible `run_daily_digest.py` prompt and any file-access prompt, or install with `--allow-claude-commands --allow-claude-state-read` to explicitly add one global command allow rule and one `.state` read directory.

## First Run

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py
```

On first run, a dedicated browser profile opens. Log in to X once in that browser. Later runs reuse the saved profile and default to headless collection.

## Data Collection Sources

There are three collection entry points:

```bash
# Browser-only collector
python3 twitter-digest/scripts/browser_x_digest.py --include-dms

# API-only collector, requires OAuth2 user-context credentials or --bearer-token
X_BEARER_TOKEN=... python3 twitter-digest/scripts/api_x_digest.py --handle <handle>

# Recommended upper-level wrapper
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py
```

`run_daily_digest.py` defaults to `--source auto`:

- If `X_BEARER_TOKEN` or `TWITTER_BEARER_TOKEN` is configured, it uses the API collector.
- If saved API credentials exist, it uses the API collector and does not fall back to browser on API errors.
- If no API credentials exist, it uses the browser collector.

Source isolation:

- API mode only runs `api_x_digest.py`; it never opens a browser or reads the browser profile.
- Browser mode only runs `browser_x_digest.py`; it does not use API tokens or API collector output.
- `--source auto` picks one source for the run and does not merge API and browser data.
- API DM data gaps are notes only; they do not mean browser DM data was collected.

Force a source:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --source browser
X_BEARER_TOKEN=... python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --source api --handle <handle>
```

API mode is for stable public-data collection, including the official home timeline endpoint when the configured token has user-context timeline access. API mode never starts a browser, never reads the browser profile, and never collects X Chat / DM content from the browser. Use browser mode when visible X Chat / DM is required. API DM lookup is marked TODO because XChat / encrypted DMs may not appear in `/2/dm_events`; do not use API DM to conclude there are no private messages. App-only API keys are not enough for user-context data.

## Configure API In Chat

Users should trigger every flow from chat. They do not need to export environment variables manually. Ask the agent to run:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api
```

For a local user-owned X Developer App, the supported API setup path is OAuth2 Authorization Code with PKCE. Ask the agent to run:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api
```

The script uses OAuth2 directly. It asks for the X Developer App `Client ID`, opens the X authorization page, waits for the user to authorize the account, receives the local callback, exchanges it for a user-context access token and refresh token, then saves it. In a non-interactive agent session, it opens a real Terminal window for Client ID / Secret input and closes it after the flow ends.

If the user already has an OAuth2 user access token, use the direct token path:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api-token
```

The script opens a hidden system prompt for the token, then asks for optional handle/user id and saves the config locally.

OAuth1 is no longer exposed as a normal setup path for this skill because it did not reliably return DM data during validation. Use OAuth2 with user-context scopes for API collection; otherwise rely on the browser collector.

The app's callback URL in X Developer Portal must match the redirect URI shown by the script, by default:

```text
http://127.0.0.1:8765/callback
```

For API DM lookup through OAuth2, include these scopes when configuring the X App / OAuth flow:

```text
dm.read tweet.read users.read offline.access
```

Use `dm.write` only if the app will send or delete messages; the digest skill only reads.

On macOS prompts appear as system dialogs; non-GUI terminals fall back to hidden terminal input. The token is saved to:

```text
twitter-digest/.state/api_config.json
```

The file is created with owner-only permissions where supported. Later runs of `run_daily_digest.py --source auto` read this saved config and use API automatically without opening the browser. To clear it:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/configure_api.py --clear
```

If OAuth returns a refresh token, later daily runs refresh the saved access token automatically before collection.

Chat flow summary:

```text
生成 X 日报       -> agent runs python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py
输入 X token     -> agent runs python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api-token
配置 X API       -> agent runs python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api
清除 X API 配置  -> agent runs python3 ~/.claude/skills/twitter-digest/scripts/configure_api.py --clear
调试浏览器       -> agent runs python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --source browser --headed
```

## Main Outputs

```text
twitter-digest/.state/run/digest-context.md
twitter-digest/.state/run/digest-context.json
twitter-digest/.state/run/digest-context-timeline.md
twitter-digest/.state/run/digest-context-mentions.md
twitter-digest/.state/run/digest-context-dm.md
twitter-digest/.state/run/digest-input.md
twitter-digest/.state/run/digest-input.json
```

Use `digest-context.md` as the normal AI input. Use the split context files when the agent needs only one section: timeline/profile, mentions, or DM. `digest-input.*` is raw collector capture for debugging.

During analysis/summary writing, the agent should use its file Read tool to read:

```text
~/.claude/skills/twitter-digest/.state/run/digest-context.md
~/.claude/skills/twitter-digest/.state/run/digest-context-timeline.md
~/.claude/skills/twitter-digest/.state/run/digest-context-mentions.md
~/.claude/skills/twitter-digest/.state/run/digest-context-dm.md
```

Do not use `cat`, `head`, `grep`, `python3 -c`, or temporary scripts to read context files during normal summary generation; those shell reads create extra Claude Code permission prompts.

## More Details

See:

```text
twitter-digest/DATA_COLLECTION.md
twitter-digest/RUNBOOK.md
twitter-digest/FUNCTION_RULES_FLOW.md
```
