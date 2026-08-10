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

API and X Chat configuration are required. If either is missing or broken, the wrapper opens one Terminal wizard and the current command stops with `configuration_required`. If X Chat has no passcode-backed key yet, the wizard explains how to set it in X Messages and opens that page only after confirmation. Existing passcodes get up to three local unlock attempts without repeated public-key requests. After setup finishes, rerun the digest command. It never switches to another collector.

## Data Rules

- Use only the current run's context files.
- Filter final facts to the user's local 24-hour window.
- Do not include stale mentions as pending work.
- Do not show already-replied mentions as needing reply.
- If reply status is unclear, mark it `回复状态未确认`.

## X Chat Rules

X Chat is required and uses the official API plus Chat XDK for local decryption. If Chat configuration, collection, signature verification, or decryption fails, do not generate a partial digest.

Default scanning checks at most 10 conversations with one event page each. Use `--chat-scan more` only when the user explicitly asks to see more; an explicit seven-day request uses `--chat-window-hours 168 --chat-scan more`. Stop after the first reliably decrypted conversation whose newest message is outside the window. For incomplete coverage say `X Chat 已按 X 返回顺序检查 N 个会话。`

## Summary Rubric

Produce a concise Chinese daily digest:

- 今日必须知道.
- 今日必须处理.
- Mentions.
- Timeline.
- 私信.
- 数据缺口.

Do not generate, recommend, rewrite, or send reply content. Do not take account actions.
