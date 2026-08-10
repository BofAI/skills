# Twitter Digest Data Collection

`twitter-digest` collects data through the X API only. Local profiles, cookies, and X page automation are not part of this skill.

## Supported Collector

```bash
python3 twitter-digest/scripts/api_x_digest.py
python3 twitter-digest/scripts/chat_x_digest.py
```

The chat-facing wrapper is:

```bash
python3 twitter-digest/scripts/run_daily_digest.py
```

The wrapper uses API directly.

## Configuration

API credentials are saved in:

```text
twitter-digest/.state/api_config.json
```

OAuth2 PKCE setup:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --configure
```

Verification:

```bash
python3 twitter-digest/scripts/configure_api.py --verify
```

## Runtime Contract

- Normal daily digest requests run the wrapper with no source override.
- API credentials and X Chat key configuration are required for every digest run.
- If saved API credentials exist, they are used.
- If credentials are missing or invalid, the wrapper opens API configuration. After configuration succeeds, run the digest command again.
- Public API errors are reported as failures or data gaps. X Chat API or decryption errors fail the whole digest.
- The collector never switches to another data source.

OAuth setup can open the X authorization page. That is authorization only, not collection.

## Captured Public Data

The API collector attempts to collect:

- Authenticated user profile.
- Home timeline.
- Own recent posts/profile activity.
- Mentions and handle search.
- Optional keyword search.

Public items are normalized into the current-run context. Final facts are filtered to the local 24-hour window.

## X Chat Data

X Chat is collected from `/2/chat/conversations` and conversation event history, then decrypted locally with Chat XDK. The exact 24-hour window is enforced from API event timestamps. Every listed conversation is retained: conversations without readable history are marked `unknown` and reported as a data gap. `has_message_requests` is retained only as an unverified internal diagnostic; it is never converted into a count, todo, or user-facing claim. A Chat API or decryption failure fails the whole digest.

Rules:

- Never save or request the X Chat passcode in Agent chat.
- Never generate a partial digest when required Chat collection or decryption fails.
- Browser/cookie DM collection is not part of this skill.

## Output Shape

Current-run files:

```text
.state/run/digest-input.json
.state/run/digest-input.md
.state/run/digest-context.md
.state/run/digest-context.json
.state/run/digest-context-timeline.md
.state/run/digest-context-mentions.md
.state/run/digest-context-dm.md
```

No long-term memory or daily archive is written.
