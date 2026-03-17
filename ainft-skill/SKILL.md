---
name: ainft-skill
description: "BankOfAI account query and recharge skill. Use for requests like 'recharge 1 usdt', '给 BankOfAI 充值 1 USDT', or to query BankOfAI balance/orders. Recharge uses the remote MCP endpoint https://recharge.bankofai.io/mcp with the single `recharge` tool."
version: 1.1.1
dependencies:
  - node >= 18.0.0
  - x402-recharge-server MCP (https://recharge.bankofai.io/mcp)
tags:
  - bankofai
  - balance
  - orders
  - recharge
  - mcp
  - usdt
  - trc20
---

# BankOfAI Skill

This skill owns the local BankOfAI account query layer and the remote BankOfAI recharge flow. The server must not store the user's account API key.

## When To Use

Use this skill for requests such as:

- `recharge 1 usdt`
- `recharge my BankOfAI account with 1 usdt`
- Chinese requests such as `给 BankOfAI 充值 1 USDT`
- Chinese requests such as `通过 https://recharge.bankofai.io/mcp 给 BankOfAI 充值 1 usdt`
- `check my BankOfAI balance`
- `list my BankOfAI orders`

## Scope

- The BankOfAI API key is managed by the local agent / skill.
- Balance and order queries should call BankOfAI directly from local scripts.
- Recharge and payment flows should use the remote MCP endpoint `https://recharge.bankofai.io/mcp`.
- Use the MCP tool `recharge` for all supported recharge routes such as `USDT`.
- Do not use native `TRX` recharge flows from this skill.
- If the requested token is not a supported TRC20 token, return the server validation error to the user.

## Recharge Flow

For a request like `recharge 1 usdt`, use the remote MCP endpoint directly and call:

- `recharge(amount="1", token="USDT")`

Return the settlement status, transaction hash, token, and amount to the user after the MCP call completes.

## Local Configuration

This skill is configured for BankOfAI production.

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
