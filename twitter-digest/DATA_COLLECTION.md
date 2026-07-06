# Twitter Digest Data Collection

`twitter-digest` collects data through the X API only. Local profiles, cookies, and X page automation are not part of this skill.

## Supported Collector

```bash
python3 twitter-digest/scripts/api_x_digest.py
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
python3 twitter-digest/scripts/run_daily_digest.py --configure-api
```

Existing token setup:

```bash
python3 twitter-digest/scripts/run_daily_digest.py --configure-api-token
```

Verification:

```bash
python3 twitter-digest/scripts/configure_api.py --verify
```

## Runtime Contract

- Normal daily digest requests run the wrapper with no source override.
- API credentials are required for every digest run.
- If saved API credentials exist, they are used.
- If credentials are missing or invalid, the wrapper opens API configuration. After configuration succeeds, run the digest command again.
- API errors are reported as failures or data gaps.
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

## DM Data

The API may expose DM events for some accounts, but X Chat/encrypted messages are often incomplete or absent.

Rules:

- Never claim "no DMs" from zero API DM events.
- Treat API DM failures as data gaps.
- Non-API DM collection is not part of this skill.

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
