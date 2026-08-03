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
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure
python3 ~/.codex/skills/twitter-digest/scripts/run_daily_digest.py --configure
```

Verify API:

```bash
python3 ~/.claude/skills/twitter-digest/scripts/configure_api.py --verify
python3 ~/.codex/skills/twitter-digest/scripts/configure_api.py --verify
```

## Source Selection

The wrapper uses API directly.

API and X Chat configuration are required. If either is missing or broken, the wrapper opens one Terminal wizard and the current command stops with `configuration_required`. The wizard asks for Client ID, Client Secret, and X Chat passcode as needed and skips valid existing state. After it finishes, rerun the digest command. It never switches to another collector.

## Data Rules

- Use only the current run's context files.
- Filter final facts to the user's local 24-hour window.
- Do not include stale mentions as pending work.
- Do not show already-replied mentions as needing reply.
- If reply status is unclear, mark it `回复状态未确认`.

## X Chat Rules

X Chat is required and uses the official API plus Chat XDK for local decryption. If Chat configuration, collection, signature verification, or decryption fails, do not generate a partial digest.

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
