---
name: twitter-digest
description: Use when the user asks to generate an X/Twitter daily digest, says “生成X日报”, “X日报”, “推特日报”, or “Twitter digest”, or wants analysis of their mentions, home timeline, reply opportunities, and encrypted X Chat.
---

# X/Twitter Digest

## Overview

Generate a concise Chinese digest by invoking the bundled BofAI-patched xurl directly. This is the `@bankofai/xurl` fork with the per-user X Chat public-key fix, not the unmodified official xurl. It owns OAuth, API requests, X Chat keys, signature verification, and local decryption. The skill never reads files under `~/.xurl` and creates no persistent run files.

## Runtime

Resolve `XURL` to the binary installed beside this skill:

```bash
# Codex
XURL="$HOME/.codex/skills/twitter-digest/bin/xurl"

# Claude Code
XURL="$HOME/.claude/skills/twitter-digest/bin/xurl"
```

When the skill is loaded from another directory, use the `bin/xurl` next to that `SKILL.md`.

Require `xurl 1.3.2-beta.2` or a later BofAI release containing the per-user X Chat public-key fix and empty-event normalization:

```bash
"$XURL" version
"$XURL" auth status
```

Invoke xurl directly. Do not create or run a digest wrapper, collector, or separate crypto tool.

## Normal Run

Treat a digest request as a read-only operation. Start collecting immediately unless xurl is missing or unauthenticated.

First record the user's exact local time:

```bash
date '+%Y-%m-%d %H:%M:%S %Z %z'
```

Set `now` to that instant and `cutoff = now - 24 hours`. Every public or Chat fact in the digest must have a parseable timestamp inside `[cutoff, now]` after conversion to the user's local timezone.

### Account and public collection

Run all commands below. Detect `<handle>` from `whoami`.

```bash
"$XURL" whoami
"$XURL" timeline -n 100
"$XURL" mentions -n 100
"$XURL" posts <handle> -n 100
"$XURL" search "from:<handle>" -n 100
"$XURL" search "@<handle>" -n 100
"$XURL" search "to:<handle>" -n 100
```

Optional keyword searches may be added when the user names topics. Search operators are only a coarse prefilter; always enforce the exact timestamp window on returned items.

Mandatory rules:

- Attempt every command above before drafting.
- Exclude out-of-window and unparseable items from time-bound claims.
- Never use result ordering or a “recent” label as timestamp proof.
- A mention is pending only after checking later posts and relevant `from:<handle> to:<author>` search results.
- Classify each actionable mention as `already_replied`, `not_replied_found`, or `reply_unverified` before summarizing it.
- Only `not_replied_found` may be presented as a reply task. Describe `reply_unverified` as `回复状态未确认`.

### Encrypted X Chat

Check local key availability and list the inbox:

```bash
"$XURL" chat keys status
"$XURL" chat conversations -n 100 --json
```

Read at most 20 relevant conversations and always suppress the read receipt:

```bash
"$XURL" chat read <conversation-id> -n 100 --json --no-mark-read
```

Chat rules:

- Apply the same exact local 24-hour window to decrypted event timestamps.
- Scan at most 20 conversations and stop after three consecutive conversations contain no in-window event.
- A conversation needs a reply only when its latest in-window text came from another participant.
- If the inbox reports a pending message request, add: `需要你在 X 界面操作：打开 X → 消息 → 请求，查看发送者和内容后选择接受、删除或忽略。`
- Never infer a sender when X does not identify one.
- Treat signature or decryption warnings as a failed Chat verification, not as an empty inbox.

## Failure Contract

If a mandatory command, Chat key check, signature verification, or decryption fails, stop before writing a normal digest. Return one short capability-specific recovery action, without implementation diagnostics.

Examples:

- Missing authorization: `请先在终端完成 xurl 授权，然后重新生成日报。`
- Missing Chat keys: `请先在终端运行 xurl chat keys restore，然后重新生成日报。`
- Chat verification failure: `X Chat 验证未完成，请更新 xurl 或重新授权后再试。`
- Rate limit: state the affected capability and when to retry, then stop.

Do not expose source names, API paths, HTTP codes, app tiers, enrollment details, tokens, keys, conversation IDs, or collector internals. Do not add a collection-diagnostics appendix.

## Writing the Digest

Write in Chinese by default. Use only useful sections:

- 今日总结.
- 该处理.
- 谁 @ 了你.
- 时间线热点.
- 你的动态.
- 私信.

Keep the output focused on user-relevant facts and actions. Exclude already handled mentions from pending tasks. Do not claim that an unavailable capability contained no activity.

Never post, reply, like, repost, bookmark, follow, block, mute, send a message, accept a request, send a typing indicator, rotate Chat keys, add group members, or mark Chat read. Drafting suggestions is allowed; executing them requires a separate explicit user request and confirmation.

## X App Setup

Use these X Developer settings:

- Project access: Pay Per Use, Production.
- App permissions: **Read and write and Direct message**.
- Type of App: **Web App, Automated App or Bot**.
- Callback URI: `http://localhost:8080/callback`.
- Email permission: off.

After changing permissions, authorize again in a real Terminal. Never ask the user to paste Client ID, Client Secret, tokens, private keys, exported key blobs, or the Chat recovery PIN into Agent chat.

Use the installed binary directly:

```bash
"$XURL" auth status
"$XURL" auth oauth2 --app <app-name>
"$XURL" auth default <app-name> <username>
"$XURL" chat keys status
"$XURL" chat keys restore
```

App registration containing credentials must be performed by the operator in a real Terminal. `chat keys restore` prompts for the PIN without echo.

## Install

The beta installer supports macOS Apple Silicon/Intel and Linux amd64. It uses Node.js plus npm only during installation to acquire `@bankofai/xurl@1.3.2-beta.2`, then copies that BofAI-patched compiled binary into the skill without replacing a global xurl. It never installs or falls back to `@xdevplatform/xurl`. Normal digest runs do not require Node.js or npm.

Codex:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/main/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_CLIENT=codex sh
```

Claude Code:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/main/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_CLIENT=claude sh
```

From a checkout:

```bash
env TWITTER_DIGEST_SOURCE_DIR="$PWD/twitter-digest" /bin/sh twitter-digest/install.sh --client codex --skip-configure
```

Existing authorization and Chat keys remain managed by xurl and are reused after reinstall.

## Uninstall

Uninstall moves the installed skill, including its bundled xurl binary, into the client's `.backups` directory. It always preserves `~/.xurl`.

```bash
~/.codex/skills/twitter-digest/uninstall.sh --client codex
~/.claude/skills/twitter-digest/uninstall.sh --client claude
```
