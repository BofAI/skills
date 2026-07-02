# X/Twitter Digest

Skill for generating a Chinese daily digest from a user's own X/Twitter account. The main command is API-first: it configures X API lazily when needed, then collects through API. Browser collection is used only when explicitly requested.

## Quick Install

From a fresh checkout:

```bash
git clone git@github.com:BofAI/skills.git
cd skills
python3 twitter-digest/scripts/install.py
```

To ask Codex to install this skill for itself, paste this into Codex:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.12-beta.2/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_CLIENT=codex sh
```

When this one-line installer is launched from Codex, Claude Code, or another non-interactive agent on macOS, it opens a real Terminal window and re-runs the full installation there. This avoids agent permission/inspect prompts during `git clone`, Python checks, browser checks, and installer writes. Set `TWITTER_DIGEST_OPEN_TERMINAL=0` only when intentionally running in an already interactive Terminal or CI.

Or use the natural-language prompt:

```text
请帮我安装这个 Codex skill：

git clone git@github.com:BofAI/skills.git bofai-skills \
  && cd bofai-skills \
  && python3 twitter-digest/scripts/install.py --client codex

安装后请确认 ~/.codex/skills/twitter-digest 存在。首次运行日报时，如果缺少 X API 配置，请打开配置流程并让我完成授权；只有我明确要求浏览器模式时才打开 X 登录浏览器。
```

To ask Claude Code to install this skill for itself, paste this into Claude Code:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.12-beta.2/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_CLIENT=claude TWITTER_DIGEST_ALLOW_CLAUDE_COMMANDS=1 TWITTER_DIGEST_ALLOW_CLAUDE_STATE_READ=1 sh
```

Or use the natural-language prompt:

```text
请帮我安装这个 Claude Code skill：

git clone git@github.com:BofAI/skills.git bofai-skills \
  && cd bofai-skills \
  && python3 twitter-digest/scripts/install.py --client claude --allow-claude-commands --allow-claude-state-read

安装后请确认 ~/.claude/skills/twitter-digest 存在。首次运行日报时，如果 Claude Code 弹出 Bash 授权，批准 `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py`；如果缺少 X API 配置，请打开配置流程并让我完成授权。只有我明确要求浏览器模式时才打开 X 登录浏览器。
```

The installer chooses the target by client:

```text
Codex: ~/.codex/skills/twitter-digest
Claude Code: ~/.claude/skills/twitter-digest
```

It also checks for Python 3.9+ and a supported Chromium browser: Google Chrome, Chromium, Microsoft Edge, or Brave. The installer does not install or upgrade Python or browsers; if a prerequisite is missing, install it and rerun the same install command.
Reinstalling is the upgrade path: it replaces the skill code and preserves the existing installed `.state` directory, including saved API and browser-session settings. The installer still excludes `.state` from the development checkout.
After installation, run the installed copy. If a script is accidentally started from a temporary clone while an installed copy exists, it automatically re-runs the installed copy so state is saved under `~/.claude/skills/twitter-digest/.state` or `~/.codex/skills/twitter-digest/.state`.

## Uninstall

Safe uninstall moves the installed skill to `.backups/` and preserves `.state`:

```bash
~/.codex/skills/twitter-digest/uninstall.sh --client codex
~/.claude/skills/twitter-digest/uninstall.sh --client claude
```

To permanently remove the installed skill and `.state`, add `--purge-state`.

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

On first run, the script checks X API configuration. If API credentials are missing or authentication is broken, it opens the API configuration flow and then continues collection. Use `--source browser` only when you explicitly want local browser collection.

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

- A normal daily run uses API.
- If API credentials are missing or authentication is broken, it opens API configuration and then retries API collection once.
- Use `--source browser` only when the user explicitly wants browser collection.

Source isolation:

- API mode only runs `api_x_digest.py`; it never opens a browser or reads the browser profile.
- Browser mode only runs `browser_x_digest.py`; it does not use API tokens or API collector output.
- Default `--source auto` picks one source for the run and does not merge API and browser data.
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

OAuth1 is no longer exposed as a normal setup path for this skill because it did not reliably return DM data during validation. Use OAuth2 with user-context scopes for API collection; use explicit browser mode when visible X Chat / DM collection is required.

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

The file is created with owner-only permissions where supported. Later normal runs read this saved config and use API without opening the browser. Use `run_daily_digest.py --source browser` only when the user explicitly wants browser collection. To clear API config:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/configure_api.py --clear
```

If OAuth returns a refresh token, later API-source runs refresh the saved access token automatically before collection. If refresh/authentication fails, the main collection command reopens API configuration and retries once.

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
