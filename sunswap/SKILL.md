---
name: SunSwap DEX Trading
description: Execute token swaps, manage liquidity, and query market data on SunSwap DEX via the sun-cli.
version: 3.0.1
dependencies:
  - "@bankofai/sun-cli"
tags:
  - defi
  - dex
  - swap
  - liquidity
  - tron
  - sunswap
---

# SunSwap DEX Trading Skill

## Quick Start

This skill enables AI agents to interact with SunSwap DEX on the TRON blockchain through `sun-cli` — a unified CLI for quoting swaps, executing trades, managing liquidity (V2/V3/V4), querying pools, prices, positions, and more.

### Prerequisites

1. **Install sun-cli** (globally):
   ```bash
   npm install -g @bankofai/sun-cli
   ```

2. **Configure wallet** (required for write operations only):
   ```bash
   export TRON_PRIVATE_KEY="your_private_key_here"
   # or
   export TRON_MNEMONIC="word1 word2 word3 ..."
   # or
   export AGENT_WALLET_PASSWORD="your_agent_wallet_password"
   ```

3. **Optional environment variables:**
   ```bash
   export TRON_NETWORK=mainnet          # mainnet | nile | shasta (default: mainnet)
   export TRONGRID_API_KEY=your_key     # recommended for mainnet
   ```

Read-only commands (price, quote, pool list, etc.) work without wallet credentials.

---

## AI Agent Flags

Always use these flags when calling `sun` from an AI agent:

| Flag | Purpose |
|------|---------|
| `--json` | Machine-readable JSON output to stdout |
| `--yes` | Skip interactive confirmation prompts |
| `--dry-run` | Simulate write operations without sending transactions |
| `--fields <list>` | Limit output to specific fields (reduce token usage) |
| `--network <net>` | Override network: `mainnet`, `nile`, `shasta` |

**Standard agent invocation pattern:**
```bash
sun --json --yes [command] [args] [options]
```

> **WARNING: `--network` only accepts `mainnet`, `nile`, or `shasta`.**
> Invalid network names (e.g. `badnet`) will silently fall back to mainnet without error.
> The AI agent must validate the network value before passing it.

> **WARNING: `--dry-run` only builds a transaction preview.**
> It does NOT check balances, validate fee tiers, verify tick alignment, or reject
> same-token swaps. The agent must perform these validations before executing.
> See [Agent Pre-Validation Checklist](#agent-pre-validation-checklist) below.

---

## Agent Pre-Validation Checklist

Before executing any write operation (`swap`, `liquidity`, `contract send`), the AI agent **must** perform the following checks. The CLI's `--dry-run` does not validate these — it only builds a transaction preview.

### Before Swap

1. **Check balance is sufficient:**
   ```bash
   sun --json wallet balances
   ```
   Compare the token balance against the `amountIn`. Abort if insufficient.

2. **Verify tokenIn ≠ tokenOut:**
   Same-token swaps (e.g. TRX → TRX) are not rejected by `--dry-run`. The agent must check that the two tokens are different before executing.

3. **Validate slippage is reasonable:**
   Recommended range: 0.001 (0.1%) to 0.05 (5%). Warn the user if outside this range.

### Before V3 Liquidity (Mint)

1. **Use only valid fee tiers:** `100`, `500`, `3000`, or `10000`.
   Invalid fee values (e.g. 9999) are not rejected by `--dry-run`.

2. **Ensure ticks are aligned to tick spacing:**

   | Fee Value | Tick Spacing | Valid tick examples |
   |-----------|-------------|---------------------|
   | 100       | 1           | any integer         |
   | 500       | 10          | -10, 0, 10, 20     |
   | 3000      | 60          | -120, -60, 0, 60   |
   | 10000     | 200         | -400, -200, 0, 200 |

   Both `--tick-lower` and `--tick-upper` must be exact multiples of the tick spacing.
   Misaligned ticks are not rejected by `--dry-run` but will fail on-chain.

3. **Check balance is sufficient** for both token0 and token1 amounts.

### Before V2 Liquidity (Add)

1. **Check balance is sufficient** for both token-a and token-b amounts.

### General

- **Validate `--network`** is one of: `mainnet`, `nile`, `shasta`. Invalid values silently fall back to mainnet.
- **Validate `--type`** for `tx scan` is one of: `swap`, `add`, `withdraw`. Invalid values return empty results instead of errors.

---

## Command Reference

### 1. Wallet

Check wallet address and token balances.

```bash
# Show wallet address
sun --json wallet address

# Check all balances
sun --json wallet balances

# Check specific owner and tokens
sun --json wallet balances --owner TAddress --tokens TRX,USDT
```

---

### 2. Token Price

Fetch token prices from SUN.IO.

```bash
# Price by symbol
sun --json price TRX

# Price by address
sun --json price --address TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t

# Multiple tokens
sun --json price USDT
```

---

### 3. Swap Quote (Read-Only)

Get a price quote without executing. No wallet required.

```bash
sun --json swap:quote <tokenIn> <tokenOut> <amountIn>
```

**Parameters:**
- `tokenIn` / `tokenOut`: Token symbol (TRX, USDT, etc.) or TRC20 address
- `amountIn`: Amount in sun (smallest unit, e.g. 1000000 = 1 TRX)

**Examples:**
```bash
# Quote 100 TRX → USDT
sun --json swap:quote TRX USDT 100000000

# Quote with all route details
sun --json swap:quote TRX USDT 100000000 --all

# Quote on nile testnet
sun --json swap:quote TRX USDT 100000000 --network nile
```

---

### 4. Execute Swap

Execute a token swap through the SunSwap Universal Router.

```bash
sun --json --yes swap <tokenIn> <tokenOut> <amountIn> [--slippage <pct>]
```

**Parameters:**
- `tokenIn` / `tokenOut`: Token symbol or TRC20 address
- `amountIn`: Amount in sun (smallest unit)
- `--slippage`: Slippage tolerance as decimal (default: 0.005 = 0.5%)

**Examples:**
```bash
# Swap 100 TRX to USDT
sun --json --yes swap TRX USDT 100000000

# Swap with custom slippage
sun --json --yes swap TRX USDT 100000000 --slippage 0.01

# Dry-run (simulate without sending)
sun --json --yes --dry-run swap TRX USDT 100000000

# Use contract addresses
sun --json --yes swap T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t 100000000
```

---

### 5. V2 Liquidity

Add or remove liquidity on SunSwap V2 AMM pools.

#### Add Liquidity
```bash
sun --json --yes liquidity v2:add \
  --token-a <token> --token-b <token> \
  --amount-a <amount> [--amount-b <amount>] \
  [--min-a <min>] [--min-b <min>] \
  [--to <recipient>] [--deadline <seconds>]
```

**Examples:**
```bash
# Add TRX + USDT liquidity
sun --json --yes liquidity v2:add --token-a TRX --token-b USDT --amount-a 1000000 --amount-b 290000

# Only specify one side (auto-calculate the other)
sun --json --yes liquidity v2:add --token-a TRX --token-b USDT --amount-a 1000000

# Dry-run first
sun --json --yes --dry-run liquidity v2:add --token-a TRX --token-b USDT --amount-a 1000000
```

#### Remove Liquidity
```bash
sun --json --yes liquidity v2:remove \
  --token-a <token> --token-b <token> \
  --liquidity <raw_amount> \
  [--min-a <min>] [--min-b <min>] \
  [--to <recipient>] [--deadline <seconds>]
```

**Examples:**
```bash
# Remove liquidity
sun --json --yes liquidity v2:remove --token-a TRX --token-b USDT --liquidity 500000

# Dry-run first
sun --json --yes --dry-run liquidity v2:remove --token-a TRX --token-b USDT --liquidity 500000
```

---

### 6. V3 Liquidity (Concentrated)

Manage concentrated liquidity positions on SunSwap V3.

**Fee tiers (only these values are valid):**

| Fee Rate | Fee Value | Tick Spacing | Full Range Ticks |
|----------|-----------|-------------|------------------|
| 0.01%    | 100       | 1           | -887272 / 887272 |
| 0.05%    | 500       | 10          | -887270 / 887270 |
| 0.3%     | 3000      | 60          | -887220 / 887220 |
| 1%       | 10000     | 200         | -887200 / 887200 |

> **IMPORTANT:** `--fee` must be exactly one of: `100`, `500`, `3000`, `10000`.
> Other values (e.g. 9999) are NOT rejected by `--dry-run` but will fail on-chain.
>
> `--tick-lower` and `--tick-upper` must be exact multiples of the tick spacing for the chosen fee tier.
> Misaligned ticks are NOT rejected by `--dry-run` but will fail on-chain.

#### Mint New Position
```bash
sun --json --yes liquidity v3:mint \
  --token0 <token> --token1 <token> \
  [--fee <100|500|3000|10000>] \
  [--tick-lower <N>] [--tick-upper <N>] \
  [--amount0 <amount>] [--amount1 <amount>] \
  [--recipient <address>] [--deadline <seconds>]
```

**Examples:**
```bash
# Mint with full-range defaults
sun --json --yes liquidity v3:mint --token0 TRX --token1 USDT --amount0 1000000

# Mint with specific fee and tick range (ticks aligned to spacing=60 for fee=3000)
sun --json --yes liquidity v3:mint \
  --token0 TRX --token1 USDT --fee 3000 \
  --tick-lower -887220 --tick-upper 887220 \
  --amount0 1000000
```

#### Increase Position
```bash
sun --json --yes liquidity v3:increase --token-id <id> --amount0 <amount> [--amount1 <amount>]
```

#### Decrease Position
```bash
sun --json --yes liquidity v3:decrease --token-id <id> --liquidity <raw_amount> [--min0 <min>] [--min1 <min>]
```

#### Collect Fees
```bash
sun --json --yes liquidity v3:collect --token-id <id> [--recipient <address>]
```

---

### 7. V4 Liquidity

Manage liquidity on SunSwap V4 pools (with hooks support).

#### Mint New Position
```bash
sun --json --yes liquidity v4:mint \
  --token0 <token> --token1 <token> \
  [--fee <fee>] \
  [--tick-lower <N>] [--tick-upper <N>] \
  [--amount0 <amount>] [--amount1 <amount>] \
  [--slippage <pct>] [--recipient <address>] \
  [--create-pool]
```

**Examples:**
```bash
# Mint V4 position
sun --json --yes liquidity v4:mint --token0 TRX --token1 USDT --amount0 1000000

# Create pool if not exists
sun --json --yes liquidity v4:mint --token0 TRX --token1 USDT --amount0 1000000 --create-pool
```

#### Increase / Decrease / Collect
```bash
# Increase
sun --json --yes liquidity v4:increase --token-id <id> --token0 TRX --token1 USDT --amount0 500000

# Decrease
sun --json --yes liquidity v4:decrease --token-id <id> --liquidity <raw> --token0 TRX --token1 USDT

# Collect fees
sun --json --yes liquidity v4:collect --token-id <id>

# Query position info
sun --json liquidity v4:info --pm <positionManager> --token-id <id>
```

---

### 8. Pool Discovery

Search and inspect liquidity pools.

```bash
# List pools by token
sun --json pool list --token TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t

# Search by keyword
sun --json pool search "TRX USDT"

# Top APY pools
sun --json pool top-apy --page-size 10

# Pool volume history
sun --json pool vol-history <poolAddress> --start 2026-01-01 --end 2026-03-15

# Pool liquidity history
sun --json pool liq-history <poolAddress> --start 2026-01-01 --end 2026-03-15

# Pool hooks (V4)
sun --json pool hooks
```

---

### 9. Token Discovery

Search and list token metadata.

```bash
# List all tokens
sun --json token list

# Filter by protocol
sun --json token list --protocol V3

# Search by keyword
sun --json token search USDT
```

---

### 10. Position Management

Query user liquidity positions.

```bash
# List all user positions
sun --json position list --owner TAddress

# Filter by pool or protocol
sun --json position list --owner TAddress --protocol V3

# Pool tick info
sun --json position tick <poolAddress>
```

---

### 11. Pair Info

Resolve trading pair information.

> **NOTE:** `pair info --token` requires a contract address, not a symbol.

```bash
# By contract address (USDT)
sun --json pair info --token TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t

# By contract address (TRX)
sun --json pair info --token T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb
```

---

### 12. Protocol Analytics

Fetch protocol-level metrics.

```bash
# Snapshot
sun --json protocol info

# Historical metrics
sun --json protocol vol-history --start 2026-01-01 --end 2026-03-15
sun --json protocol users-history --start 2026-01-01 --end 2026-03-15
sun --json protocol tx-history --start 2026-01-01 --end 2026-03-15
sun --json protocol pools-history --start 2026-01-01 --end 2026-03-15
sun --json protocol liq-history --start 2026-01-01 --end 2026-03-15
```

---

### 13. Farm

Inspect SUN.IO farms.

```bash
# List farms
sun --json farm list

# Farm transactions
sun --json farm tx --owner TAddress --type stake

# User farm positions
sun --json farm positions --owner TAddress
```

---

### 14. Transaction Scan

Scan DEX transaction activity.

```bash
sun --json tx scan --type swap --token TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t --start 2026-01-01 --end 2026-03-15
```

> **IMPORTANT:** `--type` must be exactly one of: `swap`, `add`, `withdraw`.
> Invalid types (e.g. `invalidtype`) return empty results instead of an error.
> The agent must validate the type value before passing it.

---

### 15. Generic Contract Calls

Read or send arbitrary TRON contract calls when higher-level commands are insufficient.

```bash
# Read (no wallet needed)
sun --json contract read <address> <functionName> --args '["arg1","arg2"]'

# Send (requires wallet)
sun --json --yes contract send <address> <functionName> --args '["arg1","arg2"]' --value 0
```

---

## Recommended Workflow for AI Agents

### Pattern 1: Quick Swap (Three-Step with Validation)

**Best for:** User-facing swap operations.

**Step 1 — Validate inputs (agent-side, no CLI call):**
- Confirm tokenIn ≠ tokenOut (same-token swaps like TRX→TRX are not rejected by CLI)
- Confirm `--network` is valid (`mainnet`, `nile`, or `shasta`)

**Step 2 — Check balance and get quote:**
```bash
sun --json wallet balances
sun --json swap:quote TRX USDT 100000000
```

Verify balance ≥ amountIn. Show the user: expected output amount, price impact, route.

**Step 3 — Execute after user confirms:**
```bash
sun --json --yes swap TRX USDT 100000000 --slippage 0.005
```

---

### Pattern 2: Safe Execution (Dry-Run First)

**Best for:** Large amounts or cautious operations.

> **NOTE:** `--dry-run` only previews the transaction structure. It does NOT check
> balances, validate fee tiers, or reject invalid parameters. Always check balances
> separately before proceeding to actual execution.

```bash
# Check balance first
sun --json wallet balances

# Simulate (preview transaction structure)
sun --json --yes --dry-run swap TRX USDT 100000000

# Execute after reviewing dry-run result and confirming balance
sun --json --yes swap TRX USDT 100000000
```

---

### Pattern 3: Liquidity Management (V3 Example)

**Best for:** Adding concentrated liquidity.

**Step 1 — Validate parameters (agent-side):**
- Confirm `--fee` is one of: `100`, `500`, `3000`, `10000`
- Confirm `--tick-lower` and `--tick-upper` are multiples of tick spacing (e.g. 60 for fee=3000)
- Confirm token0 ≠ token1

**Step 2 — Check balances and pool info:**
```bash
sun --json wallet balances
sun --json position list --owner TAddress --protocol V3
sun --json pool search "TRX USDT"
```

Verify balance is sufficient for both amount0 and amount1.

**Step 3 — Dry-run mint (preview only, does not validate balances or parameters):**
```bash
sun --json --yes --dry-run liquidity v3:mint \
  --token0 TRX --token1 USDT --fee 3000 \
  --tick-lower -887220 --tick-upper 887220 \
  --amount0 1000000
```

**Step 4 — Execute after user confirms:**
```bash
sun --json --yes liquidity v3:mint \
  --token0 TRX --token1 USDT --fee 3000 \
  --tick-lower -887220 --tick-upper 887220 \
  --amount0 1000000
```

---

### Pattern 4: Information Gathering

**Best for:** Answering user questions about tokens, pools, prices.

```bash
# "What's the price of TRX?"
sun --json price TRX

# "Show me the top APY pools"
sun --json pool top-apy --page-size 10

# "What are my positions?"
sun --json position list --owner TAddress

# "What pairs include USDT?"
sun --json pair info --token TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t
```

> **NOTE:** `pair info --token` requires a contract address, not a symbol.
> Use the [Supported Token Symbols](#supported-token-symbols) table to resolve symbols to addresses.

---

## Supported Token Symbols

`sun-cli` has built-in symbol resolution. Common symbols:

| Symbol | Mainnet Address | Decimals |
|--------|--------------------------------------|----------|
| TRX    | T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb | 6        |
| WTRX   | TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR | 6        |
| USDT   | TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t | 6        |
| USDC   | TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8 | 6        |
| USDD   | TPYmHEhy5n8TCEfYGqW2rPxsghSfzghPDn | 18       |
| SUN    | TSSMHYeV2uE9qYH95DqyoCuNCzEL1NvU3S | 18       |
| JST    | TCFLL5dx5ZJdKnWuesXxi1VPwjLVmWZZy9 | 18       |
| BTT    | TAFjULxiVgT4qWk6UZwjqwZXTSaGaqnVp4 | 18       |
| WIN    | TLa2f6VPqDgRE67v1736s7bJ8Ray5wYjU7 | 6        |

Any TRC20 token can also be referenced by its contract address directly.

---

## Security Rules

### CRITICAL: Never Display Private Keys

**FORBIDDEN:**
- Private keys, seed phrases, mnemonics
- Environment variable values containing secrets
- Agent wallet passwords

**ALLOWED:**
- Public wallet addresses
- Transaction hashes
- Token balances and prices

### CRITICAL: Prevent Duplicate Transactions

- One user command = one transaction
- After a successful transaction, mark it as done
- Never retry a successful transaction

### CRITICAL: Validate Inputs Before Execution

The CLI does not validate all inputs in `--dry-run` mode. The agent must:
- Verify tokenIn ≠ tokenOut before swap
- Verify `--fee` is one of: 100, 500, 3000, 10000 before V3 mint
- Verify tick values are aligned to tick spacing before V3 mint
- Verify `--network` is one of: mainnet, nile, shasta
- Check `wallet balances` to confirm sufficient funds before any write operation

### CRITICAL: Use Quote + Balance Check for High-Value Operations

```bash
sun --json wallet balances
sun --json swap:quote TRX USDT 1000000000
```

Always check balance and get a quote before executing. `--dry-run` only shows transaction structure and does NOT validate balances or parameters.

### CRITICAL: Confirm Before Write Operations

Always show the user what will happen (quote, dry-run) and get explicit confirmation before executing any write operation (swap, add/remove liquidity, contract send).

---

## User Communication Protocol

When executing trades or liquidity operations, communicate clearly:

**Before execution:**
```
Getting quote for 100 TRX → USDT...

Quote received:
  100 TRX → 15.234 USDT
  Price Impact: 0.12%
  Route: TRX → WTRX → USDT

Proceed with swap?
```

**After success:**
```
Swap completed!
  Transaction: abc123def456...
  Explorer: https://tronscan.org/#/transaction/abc123def456...
  Swapped: 100 TRX → 15.234 USDT
```

---

## Known Limitations

These are CLI-level behaviors that the AI agent must work around:

| Issue | Affected Commands | Behavior | Agent Workaround |
|-------|-------------------|----------|------------------|
| `--dry-run` doesn't check balances | `swap`, `liquidity v2:add`, all V3/V4 ops | Returns preview even if balance is insufficient | Check `wallet balances` before executing |
| `--dry-run` doesn't validate V3 fee tiers | `liquidity v3:mint` | Accepts invalid fees like 9999 | Only pass `100`, `500`, `3000`, or `10000` |
| `--dry-run` doesn't validate tick alignment | `liquidity v3:mint` | Accepts misaligned ticks | Ensure ticks are multiples of tick spacing |
| Same-token swap not rejected | `swap` | Accepts TRX→TRX in dry-run | Verify tokenIn ≠ tokenOut before calling |
| Invalid `--network` silently falls back | All commands | Unknown network names use mainnet | Only pass `mainnet`, `nile`, or `shasta` |
| Invalid `--type` returns empty results | `tx scan` | Unknown types return empty list, no error | Only pass `swap`, `add`, or `withdraw` |
| `pair info --token` needs address | `pair info` | Symbols cause API error | Use contract addresses, not symbols |

---

## Troubleshooting

### "sun: command not found"
```bash
npm install -g @bankofai/sun-cli
```

### "Wallet not configured"
Set one of: `TRON_PRIVATE_KEY`, `TRON_MNEMONIC`, or `AGENT_WALLET_PASSWORD`.

### "Network error" or "Timeout"
- Check internet connectivity
- For mainnet, set `TRONGRID_API_KEY`
- Retry (network may be congested)

### Transaction fails
- Ensure sufficient TRX for gas (100+ TRX recommended)
- Increase slippage: `--slippage 0.01`
- Verify token balance with `sun --json wallet balances`

---

**Version**: 3.0.1 (sun-cli based)
**Last Updated**: 2026-03-18
**Maintainer**: Bank of AI Team
