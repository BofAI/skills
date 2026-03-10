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
