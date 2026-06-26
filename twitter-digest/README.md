# X/Twitter Digest

Browser-only skill for generating a Chinese daily digest from a user's own X/Twitter account.

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

Use `digest-context.md` as the normal AI input. `digest-input.*` is raw browser capture for debugging.

## More Details

See:

```text
twitter-digest/RUNBOOK.md
twitter-digest/FUNCTION_RULES_FLOW.md
```
