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
