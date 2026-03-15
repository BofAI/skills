---
name: ainft-skill
description: "AINFT balance/order query and TRC20 topup skill. Use for requests like 'ainft topup 1 usdt', '给 AINFT 充值 1 USDT', or to query AINFT balance/orders. Recharge uses the remote MCP endpoint https://ainft-agent.bankofai.io/mcp with the single `recharge` tool."
version: 1.1.1
dependencies:
  - node >= 18.0.0
  - ainft-merchant MCP (https://ainft-agent.bankofai.io/mcp)
tags:
  - ainft
  - balance
  - orders
  - topup
  - recharge
  - mcp
  - usdt
  - trc20
---

# AINFT Skill

This skill owns the local AINFT query layer and the remote AINFT TRC20 topup flow. The server must not store the user's `AINFT_API_KEY`.

## When To Use

Use this skill for requests such as:

- `ainft topup 1 usdt`
- `top up ainft with 1 usdt`
- Chinese requests such as `给 AINFT 充值 1 USDT`
- Chinese requests such as `通过 https://ainft-agent.bankofai.io/mcp 给 ainft 充值 1 usdt`
- `check my ainft balance`
- `list my ainft orders`

## Scope

- The `AINFT API Key` is managed by the local agent / skill.
- Balance and order queries should call AINFT directly from local scripts.
- Recharge and payment flows should use the remote MCP endpoint `https://ainft-agent.bankofai.io/mcp`.
- Use the MCP tool `recharge` for all supported TRC20 topups such as `USDT`.
- Do not use native `TRX` topups from this skill.
- If the requested token is not a supported TRC20 token, return the server validation error to the user.

## Recharge Flow

For a request like `ainft topup 1 usdt`, use the remote MCP endpoint directly and call:

- `recharge(amount="1", token="USDT")`

Return the settlement status, transaction hash, token, and amount to the user after the MCP call completes.

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
