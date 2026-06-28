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

# API-only collector, requires X_BEARER_TOKEN or --bearer-token
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

API mode is for stable public-data collection, including the official home timeline endpoint when the configured token has user-context timeline access. Browser mode is still required for X Chat / DM content unless a read-DM-capable API integration is configured.

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
