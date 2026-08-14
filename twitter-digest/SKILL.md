---
name: twitter-digest
description: Use when the user asks to generate an X/Twitter daily digest, says “生成X日报”, “X日报”, “推特日报”, or “Twitter digest”, wants analysis of their mentions, home timeline, own posts, and encrypted X Chat, or asks to switch the active X/Twitter account with phrases such as “切换X账号”, “切换Twitter账户”, or “把日报切到 @username”.
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

Require `xurl 1.3.2-beta.3` or a later BofAI release containing the per-user X Chat public-key fix and empty-event normalization:

```bash
"$XURL" version
"$XURL" auth status
```

Invoke xurl directly. Do not create or run a digest wrapper, collector, or separate crypto tool.

## Switch Account

Treat one natural-language account-switch request as a single workflow with up to two secure user interactions: browser OAuth first, then X Chat key recovery only when the selected account has no usable local key. Do not require the user to send a second Agent message between the two steps.

Use only the `XURL` binary bundled beside this skill. Never invoke a global or unmodified xurl. Resolve the registered App from `"$XURL" auth status`; prefer the current credentialed App. New installations use the fixed local App name `twitter-digest`. If no credentialed App exists, run the installer setup instead of asking for credentials in Agent chat.

When the user supplies a target handle, strip the leading `@` and preserve it as the expected username. First test whether that user's existing OAuth2 token is still valid:

```bash
"$XURL" token --app <app-name> -u <username>
"$XURL" whoami --auth oauth2 --app <app-name> -u <username>
```

Reuse the token only when `whoami` returns the expected username. Otherwise open a real Terminal and run the browser flow; omit `<username>` only when the user did not name a target account:

```bash
"$XURL" auth oauth2 <username> --app <app-name>
```

Use `--headless` only on a remote machine without a reachable local callback. Never assume that changing accounts in an existing browser session changed xurl. After OAuth, resolve the authorized username with xurl and require an exact match when the user named a target. If it does not match, keep the previous default and ask the user to authorize the intended X account.

After identity verification, select and recheck the account explicitly:

```bash
"$XURL" auth default <app-name> <username>
"$XURL" whoami --auth oauth2 --app <app-name> -u <username>
```

Then check X Chat keys for that same App and username:

```bash
"$XURL" chat keys status --auth oauth2 --app <app-name> -u <username>
```

If the status identifies a usable key on this machine, finish without prompting for a Passcode. Otherwise automatically open a real Terminal for the second secure interaction:

```bash
"$XURL" chat keys restore --auth oauth2 --app <app-name> -u <username>
```

Do not pass `--pin`, request the Passcode in Agent chat, or place it in a command. Let xurl prompt without echo; it may first ask the user to select one of the account's registered keys. After recovery, run `chat keys status` again with the same explicit App and username. Report the switch complete only after `whoami` verifies the selected account and Chat status identifies its usable local key. If no recoverable key exists, state that public account access is authorized and ask the user to enable X Chat in an official X client before retrying key recovery.

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

Record `self_user_id` from `whoami.data.id`. This exact ID is also the only authority for deciding X Chat message direction.

Optional keyword searches may be added when the user names topics. Search operators are only a coarse prefilter; always enforce the exact timestamp window on returned items.

Mandatory rules:

- Attempt every command above before writing the digest.
- Exclude out-of-window and unparseable items from time-bound claims.
- Never use result ordering or a “recent” label as timestamp proof.
- A mention is pending only after checking later posts and relevant `from:<handle> to:<author>` search results.
- Classify each actionable mention as `already_replied`, `not_replied_found`, or `reply_unverified` before summarizing it.
- Use reply classification only to report whether a mention is still pending. Only `not_replied_found` may be labeled `尚未回复`; describe `reply_unverified` as `回复状态未确认`. Never recommend what to reply or provide reply wording.

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
- If `chat read` exits successfully, stderr has no public-key, signature, verification, or decryption warning, and stdout is exactly the JSON value `null`, normalize that result to the empty event array `[]`. Do not apply this normalization to any other malformed or failed response.
- Sort `Message` events by `created_at_msec` before reading or summarizing them. Ignore `ReadReceipt`, `KeyChange`, and other event types when reconstructing message content.
- For every `Message`, classify direction only from IDs: `sender_id == self_user_id` means `我发送`; a different `sender_id` that belongs to the conversation means `对方发送`. Never infer direction from event order, participant array order, display names, content, read receipts, or which side spoke first.
- For `Text` content, inspect the text plus top-level `attachments` and `media_hashes` before deciding what the message contains. A blank text with an attachment is a media-only message, not an empty message.
- For an attachment with `attachment_type: "media"`, map `media_type` as `1=图片`, `2=GIF`, `3=视频`, `4=音频`, `5=文件`, and `6=SVG`. State `你发送了一个 GIF` or `对方发送了一张图片` according to the already-verified direction. Use `媒体附件` when the attachment type is present but cannot be resolved. Do not download media during a digest.
- Treat `Reaction` content as an emoji reaction to another message, not as empty text and not as a new reply-status signal. Ignore `ReactionRemoved` for digest content.
- If a `Message` has no text, attachment, media hash, or recognized reaction, omit it entirely. Never write `空消息` or use that event to decide reply status.
- Resolve other senders' display names only after direction is known. If a sender cannot be resolved to a conversation participant, label the sender `未确认` and do not use that event to decide reply status.
- When both sides have in-window content-bearing messages, preserve their chronological sequence and represent both sides in the summary. Never omit one side in a way that reverses who said what.
- Determine reply status from the latest verified in-window content-bearing `Message`, where content is non-empty text or a recognized attachment/media hash. If it is `对方发送`, report that the other person sent the latest message without proposing a response. If it is `我发送`, state when the user last sent content and say `可以先等对方回复`. Do not use reactions, truly empty messages, or non-message events to infer reply status.
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

Use a natural, restrained, executive-friendly editorial voice:

- Lead with what happened and why it matters; separate observed facts from recommendations.
- Phrase uncertainty as uncertainty. Do not label a message as a scam, template, or manipulation tactic without explicit evidence.
- For promotional content containing an unfamiliar link, prefer: `消息包含推广内容和外部短链；如需打开，建议先核验链接来源。`
- For a conversation whose latest message is the user's, prefer: `你在 <time> 已回复，可以先等对方回复。`
- Avoid internal or mechanical wording such as `窗口内`, `命中`, `见第 N 项`, `零产出`, `无实质信息`, `无需你动作`, `球在你这边`, or `会话性质建议你自己确认`. Translate collection results into reader-facing prose.
- Never include public engagement metrics such as like, reply, repost, quote, bookmark, view, impression, or follower counts. Do not rank or recommend posts by engagement.
- Never draft, suggest, paraphrase, or offer to draft a public reply or private message as part of a digest. Do not write phrases such as `回一句即可`, `建议回复`, or `需要我起草`.
- Include counts only when they help the user understand activity or priority. Do not narrate repeated runs, elapsed time since another digest, or suggest `/loop` or scheduling in a digest postscript.
- End after the last useful section; do not add process commentary or an unsolicited follow-up pitch.

Never add collection-completeness disclaimers or diagnostic sections to a digest. When the Failure Contract applies, return only the short recovery action and stop instead of attaching a partial digest or diagnostics appendix.

Never post, reply, like, repost, bookmark, follow, block, mute, send a message, accept a request, send a typing indicator, rotate Chat keys, add group members, or mark Chat read. Only consider drafting after a new, separate, explicit user request; never offer it from a digest.

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

App registration containing credentials must be performed interactively in a real Terminal. The installer guides this flow when authorization is missing. Never request credentials in Agent chat. `chat keys restore` prompts for the PIN without echo.

## Install

Twitter Digest and xurl use independent versions. This skill release is `v1.5.14-beta.18`; its installer pins the separate dependency `@bankofai/xurl@1.3.2-beta.3`. The beta installer supports macOS Apple Silicon/Intel and Linux amd64. It uses Node.js plus npm only during installation, verifies the installed Bank of AI package identity and binary, then copies that compiled binary into the skill without replacing a global xurl. It never installs or falls back to `@xdevplatform/xurl`. Normal digest runs do not require Node.js or npm.

After installation, the installer reuses valid OAuth2 authorization. If no App is registered, it prompts only for the OAuth2 Client ID and Client Secret in the real Terminal; the xurl-local App name is fixed to `twitter-digest` and the callback is fixed to `http://localhost:8080/callback`. It then launches xurl's browser OAuth flow and sets the authorized account as default. It also checks X Chat keys and offers to restore an existing key. xurl cannot create or register a new X Chat key; when the account has no recoverable key, first enable X Chat in an official X client.

Codex:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.14-beta.18/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_REF=v1.5.14-beta.18 TWITTER_DIGEST_INSTALL_CLIENT=codex sh
```

Claude Code:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/v1.5.14-beta.18/twitter-digest/install.sh | env TWITTER_DIGEST_INSTALL_REF=v1.5.14-beta.18 TWITTER_DIGEST_INSTALL_CLIENT=claude sh
```

From a checkout:

```bash
env TWITTER_DIGEST_SOURCE_DIR="$PWD/twitter-digest" /bin/sh twitter-digest/install.sh --client codex --skip-configure
```

Existing authorization and Chat keys remain managed by xurl and are reused after reinstall. Managed installations may pass `--skip-configure` to bypass the interactive OAuth and Chat key checks.

## Uninstall

Uninstall moves the installed skill, including its bundled xurl binary, into the client's `.backups` directory. It always preserves `~/.xurl`.

```bash
~/.codex/skills/twitter-digest/uninstall.sh --client codex
~/.claude/skills/twitter-digest/uninstall.sh --client claude
```
