---
name: TRC20 Token Toolkit
description: Universal TRC20 token operations — transfer, approve, query balances, and fetch metadata.
version: 1.0.0
dependencies:
  - node >= 18.0.0
  - tronweb
tags:
  - trc20
  - token
  - tron
  - transfer
  - utility
---

# TRC20 Token Toolkit

Universal TRC20 token operations for AI agents on TRON. Check balances, transfer tokens, manage approvals, and fetch metadata for any TRC20 token. Supports symbol-based lookups for common tokens (USDT, USDD, SUN, etc.) and direct contract addresses for any token.

---

## Quick Start

1. Install dependencies:
   ```bash
   cd trc20-toolkit && npm install
   ```
2. Set environment variables:
   ```bash
   export TRON_PRIVATE_KEY="<your-private-key>"
   export TRON_NETWORK="mainnet"
   export TRONGRID_API_KEY="<optional>"
   ```

> [!CAUTION]
> **Never display or log the private key.**

---

## Available Scripts

### 1. `info.js` — Token Metadata

```bash
node scripts/info.js <tokenAddressOrSymbol>
node scripts/info.js USDT
node scripts/info.js TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t
```

**Output:** `name`, `symbol`, `decimals`, `total_supply`

### 2. `balance.js` — Token Balances

```bash
# Single token balance
node scripts/balance.js USDT
node scripts/balance.js USDT TWalletAddress123

# Batch balance check
node scripts/balance.js --batch USDT,USDD,SUN
node scripts/balance.js --batch USDT,USDD TWalletAddress123
```

**Output:** `trx_balance`, `tokens[]` (each with `symbol`, `balance`, `decimals`)

### 3. `transfer.js` — Transfer Tokens

| Parameter | Required | Description |
|---|---|---|
| `token` | **Yes** | Token address or symbol |
| `toAddress` | **Yes** | Recipient TRON address |
| `amount` | **Yes** | Human-readable amount |
| `--dry-run` | No | Validate only, no transaction |

```bash
node scripts/transfer.js USDT TRecipientAddress 10.5 --dry-run
node scripts/transfer.js USDT TRecipientAddress 10.5
```

**Output:** `status`, `tx_id`, `amount`, `symbol`

### 4. `approve.js` — Manage Allowances

```bash
# Set allowance
node scripts/approve.js USDT TSpenderAddress 1000 --dry-run
node scripts/approve.js USDT TSpenderAddress max

# Check current allowance
node scripts/approve.js USDT TSpenderAddress --check
node scripts/approve.js USDT TSpenderAddress --check TWalletAddress
```

**Output:** `allowance`, `is_max`, `status`, `tx_id`

---

## Usage Patterns

### Pattern 1: Check Before Transfer (Recommended)

```bash
node scripts/balance.js USDT
node scripts/transfer.js USDT TRecipient 100 --dry-run
# Confirm with user
node scripts/transfer.js USDT TRecipient 100
```

### Pattern 2: Portfolio Overview

```bash
node scripts/balance.js --batch USDT,USDD,SUN,JST,BTT
```

---

## Security Rules

> [!CAUTION]

1. **Never display private keys** in output or logs.
2. **Never transfer without user confirmation.** Always use `--dry-run` first.
3. **Prevent self-transfers.** The script rejects transfers to the sender's own address.
4. **Validate addresses.** Ensure all addresses start with `T` and are valid TRON base58 addresses.
5. **Check balances before transfer.** The script validates sufficient balance automatically.

---

## Supported Tokens

Common tokens resolved by symbol: `USDT`, `USDD`, `USDC`, `WTRX`, `SUN`, `JST`, `BTT`, `WIN`.
Any TRC20 token can be used via its contract address.

See `resources/well_known_tokens.json` for the full list.

---

## Common Issues

| Problem | Solution |
|---|---|
| `Unknown token symbol` | Use the full contract address instead |
| `Insufficient balance` | Check balance first with `balance.js` |
| `TRON_PRIVATE_KEY required` | Set the environment variable |
| `Cannot find module 'tronweb'` | Run `npm install` |

---

*Version 1.0.0 — Created by [M2M Agent Registry](https://m2mregistry.io) for Bank of AI*
