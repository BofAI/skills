# X/Twitter Digest

Generate Chinese daily or weekly digests for a user's own X/Twitter account.

The current design is MCP-first:

- Public/account data is read through the hosted X MCP.
- X Chat/DM content is read through a local logged-in browser profile.
- There is no local public-data API collector; the agent summarizes MCP tool results directly.

## Structure

```text
twitter-digest/
  SKILL.md                         agent-facing rules
  references/x-twitter-digest.md   implementation notes and scoring rules
  scripts/collect_browser_dm.py    CLI collector for visible X Chat/DM
  scripts/install.py               install into ~/.codex or ~/.claude skills
  lib/browser_dm_core.py           internal browser/CDP implementation
  .state/                          local private state, ignored on install
```

Normal agent flow:

```text
X MCP tools -> public timeline / mentions / own posts / search
browser collector -> visible X Chat / DM status and message context
agent summary -> Chinese daily or weekly report
```

## Install The Skill

From this repository's `skills/` directory, install for Codex with an explicit skills directory:

```bash
python3 twitter-digest/scripts/install.py --skills-dir ~/.codex/skills
```

For Claude Code:

```bash
python3 twitter-digest/scripts/install.py
```

The installer checks Python 3.10+ and a supported Chromium browser: Google Chrome, Chromium, Microsoft Edge, or Brave.

## Install X MCP

Install the official X API bridge:

```bash
npm install -g @xdevplatform/xurl
```

In the X Developer Portal, configure OAuth2/User authentication for your app:

- Callback / Redirect URL: `http://localhost:8080/callback`
- App permissions: `Read and write and Direct message` if you want the default broad `xurl` scopes

Register the app locally and authorize an X user:

```bash
xurl auth apps add my-app \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET \
  --redirect-uri http://localhost:8080/callback

xurl auth oauth2 --app my-app
xurl auth default my-app
```

Do not paste Client Secret or access tokens into chat. Enter them only in the local terminal.

## Configure Codex

Add the hosted X MCP to `~/.codex/config.toml`:

```toml
[mcp_servers.xapi]
command = "xurl"
args = ["mcp", "https://api.x.com/mcp"]

[mcp_servers.x-docs]
url = "https://docs.x.com/mcp"
```

For multiple X users, pin the MCP server to a username:

```toml
[mcp_servers.xapi]
command = "xurl"
args = ["mcp", "-u", "USERNAME", "https://api.x.com/mcp"]
```

Restart Codex after changing MCP config.

## Browser DM Setup

DM/X Chat should be verified through the browser collector because API/MCP DM events may not include all encrypted X Chat content.

Run once and log in if prompted:

```bash
python3 ~/.codex/skills/twitter-digest/scripts/collect_browser_dm.py
```

The collector opens a visible browser automatically when login or X Chat passcode/recovery is required. Later runs reuse the saved profile and can complete headlessly. For a forced visible browser during debugging:

```bash
python3 ~/.codex/skills/twitter-digest/scripts/collect_browser_dm.py --headed
```

## Usage

Ask the agent:

```text
用 twitter-digest 看一下我的 X 日报
```

or:

```text
生成 X 周报
```

The agent should use X MCP for public/account data and browser collection only for DM/X Chat coverage.

## Outputs

Current-run browser DM outputs are written under:

```text
twitter-digest/.state/run/
```

Important files:

```text
browser-dm-context.md
browser-dm-context.json
```

Treat `.state/` as private. It can include browser profile data and DM text.
