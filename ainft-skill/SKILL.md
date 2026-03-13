---
name: ainft-skill
description: "AINFT local skill: manage the AINFT API key and query balance and orders."
version: 1.0.0
tags:
  - ainft
  - balance
  - orders
  - trpc
---

# AINFT Skill

This skill owns the local AINFT query layer. The server must not store the user's `AINFT_API_KEY`.

## Prerequisites

- Node.js with built-in `fetch`
- A valid `AINFT_API_KEY`
- Optional local config in `ainft-config.json`, `~/.ainft/config.json`, or `~/.mcporter/ainft-config.json`

## Scope

- The `AINFT API Key` is managed by the local agent / skill.
- Balance and order queries should call AINFT directly from local scripts.
- Recharge and payment flows are outside this skill.

## Local Configuration

This skill is configured for AINFT production.

Resolution order:

1. CLI arguments
2. Environment variables
3. `ainft-config.json`
4. `~/.ainft/config.json`
5. `~/.mcporter/ainft-config.json`

See `ainft-config.example.json` for an example.

Supported fields:

- `api_key`
- `base_url`
- `timeout_ms`

Recommended production value:

- `base_url = https://chat.ainft.com`

## Available Scripts

- `node scripts/check_balance.js --format json`
  - Query the user's point balance with `api_key`
- `node scripts/check_orders.js --format json`
  - Query `order.listOrders`

### `check_balance.js`

Usage:

```bash
node scripts/check_balance.js [--api-key <key>] [--base-url <url>] [--format json|text]
```

Output:

- `json` mode returns a normalized object with `points_balance`, `summary`, `http_status`, and `config_path`
- `text` mode prints a short human-readable balance summary

### `check_orders.js`

Usage:

```bash
node scripts/check_orders.js [--api-key <key>] [--base-url <url>] [--page <n>] [--page-size <n>] [--sort-by <field>] [--order asc|desc] [--format json|text]
```

Default query options:

- `page = 1`
- `page-size = 20`
- `sort-by = createdAt`
- `order = desc`

Output:

- `json` mode returns normalized pagination fields plus `orders`
- `text` mode prints a short summary such as the number of fetched orders

## Examples

```bash
# Balance as JSON
node scripts/check_balance.js --format json

# Balance as text
node scripts/check_balance.js --format text

# Latest orders
node scripts/check_orders.js --format json

# Paged orders
node scripts/check_orders.js --page 2 --page-size 10 --format json
```

## Error Handling

- Missing credentials return an error such as `missing AINFT_API_KEY or ainft-config.json api_key`
- Unknown CLI flags cause the script to exit with a usage string on stderr
- Non-success API responses are normalized into JSON output so the caller can inspect `ok` and `http_status`
