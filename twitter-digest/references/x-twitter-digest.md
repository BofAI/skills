# X/Twitter Digest Reference

This skill is API-only.

## Commands

Normal collection:

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

## Source Selection

The wrapper uses API directly.

API configuration is required. If API config is missing or broken, the wrapper opens API configuration and retries once after configuration succeeds. It never switches to another collector.

## Data Rules

- Use only the current run's context files.
- Filter final facts to the user's local 24-hour window.
- Do not include stale mentions as pending work.
- Do not show already-replied mentions as needing reply.
- If reply status is unclear, mark it `回复状态未确认`.

## DM Rules

API DM coverage may be incomplete. Treat failed or zero DM results as a data gap, not proof that there are no DMs.

Non-API X Chat / encrypted DM collection is not part of this skill.

## Summary Rubric

Produce a concise Chinese daily digest:

- 今日总结.
- 该处理.
- 谁 @ 了你.
- 时间线热点.
- 你的动态.
- 数据缺口.
- 建议回复草稿.

Do not automatically send replies or take account actions.
