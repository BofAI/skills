# X/Twitter Digest

Skill for generating a Chinese daily digest from a user's own X/Twitter account through API collection when configured, otherwise through a saved local browser session.

## Quick Install

From a fresh checkout:

```bash
git clone git@github.com:BofAI/skills.git
cd skills/skills
python3 twitter-digest/scripts/install.py
```

For testing the current PR branch before it is merged:

```bash
git clone -b twitter-digest-skill git@github.com:BofAI/skills.git
cd skills/skills
python3 twitter-digest/scripts/install.py
```

To ask Claude Code to install this skill for itself, paste this into Claude Code:

```text
请帮我安装这个 Claude Code skill：

git clone -b twitter-digest-skill git@github.com:BofAI/skills.git /tmp/bofai-skills \
  && cd /tmp/bofai-skills/skills \
  && python3 twitter-digest/scripts/install.py

安装后请确认 ~/.claude/skills/twitter-digest 存在。首次运行日报时，如果弹出浏览器，请让我登录 X。
```

After the PR is merged, use the main branch version:

```text
请帮我安装这个 Claude Code skill：

git clone git@github.com:BofAI/skills.git /tmp/bofai-skills \
  && cd /tmp/bofai-skills/skills \
  && python3 twitter-digest/scripts/install.py

安装后请确认 ~/.claude/skills/twitter-digest 存在。首次运行日报时，如果弹出浏览器，请让我登录 X。
```

The installer copies the skill to:

```text
~/.claude/skills/twitter-digest
```

It also checks for Python 3.10+ and a supported Chromium browser: Google Chrome, Chromium, Microsoft Edge, or Brave.

## First Run

```bash
python3 twitter-digest/scripts/run_daily_digest.py
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
python3 twitter-digest/scripts/run_daily_digest.py
```

`run_daily_digest.py` defaults to `--source auto`:

- If `X_BEARER_TOKEN` or `TWITTER_BEARER_TOKEN` is configured, it uses the API collector.
- Otherwise it falls back to the browser collector.

Force a source:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --source browser
X_BEARER_TOKEN=... python3 twitter-digest/scripts/run_daily_digest.py --source api --handle <handle>
```

API mode is for stable collection, including the official home timeline endpoint when the configured token has user-context timeline access. When `--include-dms` is enabled, API mode also tries `/2/dm_events`; this requires user-context auth and DM lookup permission such as `dm.read`. App-only API keys are not enough for user-context data. If API DM lookup fails, the error is recorded as a data gap instead of being treated as an empty inbox.

## Configure API In Chat

Users should trigger every flow from chat. They do not need to export environment variables manually. Ask the agent to run:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --configure-api
```

For a local user-owned X Developer App, the supported API setup path is OAuth2 Authorization Code with PKCE. Ask the agent to run:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --configure-api
```

Then choose `OAuth2`. The script asks for the X Developer App `Client ID`, opens the X authorization page, waits for the user to authorize the account, receives the local callback, exchanges it for a user-context access token and refresh token, then saves it.

If the user already has an OAuth2 user access token, use the direct token path:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --configure-api-token
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

The file is created with owner-only permissions where supported. Later runs of `run_daily_digest.py --source auto` read this saved config and use API automatically. To clear it:

```bash
python3 twitter-digest/scripts/configure_api.py --clear
```

If OAuth returns a refresh token, later daily runs refresh the saved access token automatically before collection.

Chat flow summary:

```text
生成 X 日报       -> agent runs scripts/run_daily_digest.py
输入 X token     -> agent runs scripts/run_daily_digest.py --configure-api-token
配置 X API       -> agent runs scripts/run_daily_digest.py --configure-api
清除 X API 配置  -> agent runs scripts/configure_api.py --clear
调试浏览器       -> agent runs scripts/run_daily_digest.py --source browser --headed
```

## Test DM Collection

```bash
python3 twitter-digest/scripts/test_dm_collection.py
```

## Main Outputs

```text
twitter-digest/.state/run/digest-context.md
twitter-digest/.state/run/digest-context.json
twitter-digest/.state/run/digest-input.md
twitter-digest/.state/run/digest-input.json
```

Use `digest-context.md` as the normal AI input. `digest-input.*` is raw collector capture for debugging.

## More Details

See:

```text
twitter-digest/DATA_COLLECTION.md
twitter-digest/RUNBOOK.md
twitter-digest/FUNCTION_RULES_FLOW.md
```
