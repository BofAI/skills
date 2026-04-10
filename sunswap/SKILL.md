---
name: SunSwap DEX Trading
description: Execute token swaps, manage liquidity, and query market data on SunSwap DEX via the sun-cli.
version: 3.2.0
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

> **Wallet required:** Run `agent-wallet list` first.  
> If no wallets exist, invoke `bankofai-guide` (Section C — Wallet Guard) before proceeding.

1. **Install sun-cli** (globally):
   ```bash
   npm install -g @bankofai/sun-cli
   ```

2. **Configure wallet** (required for write operations only):
   ```bash
   export TRON_PRIVATE_KEY="your_private_key_here"
   ```
   Alternative wallet sources: `TRON_MNEMONIC` or `AGENT_WALLET_PASSWORD`.

3. **Optional environment variables:**
   ```bash
   export TRON_NETWORK=mainnet
   export TRONGRID_API_KEY=your_key
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
| `--fields` | Limit output to specific comma-separated fields |
| `--network` | Override network: `mainnet`, `nile`, `shasta` |

Standard agent invocation pattern:

```bash
sun --json price TRX
```

Write operations add `--yes` to skip prompts:

```bash
sun --json --yes swap TRX USDT 100000000
```

> **WARNING: `--network` only accepts `mainnet`, `nile`, or `shasta`.**
> Invalid network names silently fall back to mainnet without error.
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

### Before V3/V4 Position Operations (Increase/Decrease/Collect)

1. **Verify token-id exists:** Query the user's positions first:
   ```bash
   sun --json position list --owner TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW --protocol V3
   ```
   Confirm the target `--token-id` appears in the result. Passing a non-existent token-id may produce misleading errors (e.g. "amount required" instead of "position not found").

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
sun --json wallet address
```

```bash
sun --json wallet balances
```

Check balances for a specific owner address:

```bash
sun --json wallet balances --owner TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf
```

Filter by specific tokens (contract addresses only, symbols like TRX/USDT are NOT supported):

```bash
sun --json wallet balances --tokens TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t,TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR
```

> **WARNING:** `--tokens` only accepts contract addresses. Passing symbols (e.g. `TRX,USDT`) will return `Invalid contract address provided`. Use the address table in [Supported Token Symbols](#supported-token-symbols) to resolve symbols to addresses first.

---

### 2. Token Price

Fetch token prices from SUN.IO.

```bash
sun --json price TRX
```

```bash
sun --json price USDT
```

Query by contract address:

```bash
sun --json price --address TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t
```

---

### 3. Swap Quote (Read-Only)

Get a price quote without executing. No wallet required.

**Parameters:** `tokenIn` and `tokenOut` accept token symbols (TRX, USDT) or TRC20 addresses. `amountIn` is in sun (smallest unit, e.g. 1000000 = 1 TRX).

```bash
sun --json swap:quote TRX USDT 100000000
```

Quote with all route details:

```bash
sun --json swap:quote TRX USDT 100000000 --all
```

Quote on a specific network:

```bash
sun --json swap:quote TRX USDT 100000000 --network nile
```

Reverse direction:

```bash
sun --json swap:quote USDT TRX 1000000
```

---

### 4. Execute Swap

Execute a token swap through the SunSwap Universal Router.

**Parameters:** `tokenIn` and `tokenOut` accept symbols or addresses. `amountIn` is in sun. `--slippage` is a decimal (default: 0.005 = 0.5%).

```bash
sun --json --yes swap TRX USDT 100000000
```

Swap with custom slippage (1%):

```bash
sun --json --yes swap TRX USDT 100000000 --slippage 0.01
```

Dry-run (simulate without sending):

```bash
sun --json --yes --dry-run swap TRX USDT 100000000
```

Use contract addresses instead of symbols:

```bash
sun --json --yes swap T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t 100000000
```

Swap on nile testnet:

```bash
sun --json --yes swap TRX USDT 1000000 --network nile
```

---

### 5. V2 Liquidity

Add or remove liquidity on SunSwap V2 AMM pools.

**Parameters for add:** `--token-a` and `--token-b` accept symbols or addresses. `--amount-a` and `--amount-b` are in sun. Optional: `--min-a`, `--min-b`, `--to`, `--deadline`.

**Parameters for remove:** `--token-a`, `--token-b`, `--liquidity` (raw LP amount). Optional: `--min-a`, `--min-b`, `--to`, `--deadline`.

#### Add Liquidity

Single-side (auto-calculate other):

```bash
sun --json --yes liquidity v2:add --token-a TRX --token-b USDT --amount-a 1000000
```

Both sides:

```bash
sun --json --yes liquidity v2:add --token-a TRX --token-b USDT --amount-a 1000000 --amount-b 290000
```

Dry-run:

```bash
sun --json --yes --dry-run liquidity v2:add --token-a TRX --token-b USDT --amount-a 1000000
```

With minimum amounts and recipient:

```bash
sun --json --yes liquidity v2:add --token-a TRX --token-b USDT --amount-a 1000000 --amount-b 290000 --min-a 950000 --min-b 275000
```

#### Remove Liquidity

```bash
sun --json --yes liquidity v2:remove --token-a TRX --token-b USDT --liquidity 500000
```

Dry-run:

```bash
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
> Other values are NOT rejected by `--dry-run` but will fail on-chain.
>
> `--tick-lower` and `--tick-upper` must be exact multiples of the tick spacing.
> Misaligned ticks are NOT rejected by `--dry-run` but will fail on-chain.

**Parameters for mint:** `--token0`, `--token1` (symbol or address), `--fee`, `--tick-lower`, `--tick-upper`, `--amount0`, `--amount1`. Optional: `--recipient`, `--deadline`.

#### Mint New Position

Full-range with defaults:

```bash
sun --json --yes liquidity v3:mint --token0 TRX --token1 USDT --amount0 1000000
```

With specific fee and tick range (fee=3000, tick spacing=60):

```bash
sun --json --yes liquidity v3:mint --token0 TRX --token1 USDT --fee 3000 --tick-lower -887220 --tick-upper 887220 --amount0 1000000
```

Dry-run:

```bash
sun --json --yes --dry-run liquidity v3:mint --token0 TRX --token1 USDT --amount0 1000000
```

With specific fee tier (fee=500, tick spacing=10):

```bash
sun --json --yes liquidity v3:mint --token0 TRX --token1 USDT --fee 500 --tick-lower -887270 --tick-upper 887270 --amount0 1000000
```

With recipient:

```bash
sun --json --yes liquidity v3:mint --token0 TRX --token1 USDT --fee 3000 --tick-lower -60 --tick-upper 60 --amount0 1000000 --recipient TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW
```

#### Increase Position

```bash
sun --json --yes liquidity v3:increase --token-id 123 --amount0 500000
```

#### Decrease Position

```bash
sun --json --yes liquidity v3:decrease --token-id 123 --liquidity 1000
```

#### Collect Fees

```bash
sun --json --yes liquidity v3:collect --token-id 123
```

---

### 7. V4 Liquidity

Manage liquidity on SunSwap V4 pools (with hooks support).

**Parameters for mint:** `--token0`, `--token1`, `--fee`, `--tick-lower`, `--tick-upper`, `--amount0`, `--amount1`. Optional: `--slippage`, `--recipient`, `--create-pool`.

#### Mint New Position

```bash
sun --json --yes liquidity v4:mint --token0 TRX --token1 USDT --amount0 1000000
```

Create pool if it does not exist:

```bash
sun --json --yes liquidity v4:mint --token0 TRX --token1 USDT --amount0 1000000 --create-pool
```

With slippage:

```bash
sun --json --yes liquidity v4:mint --token0 TRX --token1 USDT --amount0 1000000 --slippage 0.01
```

Dry-run:

```bash
sun --json --yes --dry-run liquidity v4:mint --token0 TRX --token1 USDT --amount0 1000000
```

#### Increase Position

```bash
sun --json --yes liquidity v4:increase --token-id 123 --token0 TRX --token1 USDT --amount0 500000
```

#### Decrease Position

```bash
sun --json --yes liquidity v4:decrease --token-id 123 --liquidity 1000 --token0 TRX --token1 USDT
```

#### Collect Fees

```bash
sun --json --yes liquidity v4:collect --token-id 123
```

#### Query Position Info

```bash
sun --json liquidity v4:info --pm TLSWrv7eC1AZCXkRjpqMZUmvgd99cj7pPF --token-id 123
```

---

### 8. Pool Discovery

Search and inspect liquidity pools.

List pools by token address:

```bash
sun --json pool list --token TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t
```

Search by keyword:

```bash
sun --json pool search "TRX USDT"
```

Top APY pools:

```bash
sun --json pool top-apy --page-size 10
```

Pool volume history (requires a pool address):

```bash
sun --json pool vol-history TSUUVjysXV8YqHytSNjfkNXnnB49QDvZpx --start 2026-01-01 --end 2026-03-15
```

Pool liquidity history:

```bash
sun --json pool liq-history TSUUVjysXV8YqHytSNjfkNXnnB49QDvZpx --start 2026-01-01 --end 2026-03-15
```

Pool hooks (V4):

```bash
sun --json pool hooks
```

---

### 9. Token Discovery

Search and list token metadata.

```bash
sun --json token list
```

Filter by protocol:

```bash
sun --json token list --protocol V3
```

Search by keyword:

```bash
sun --json token search USDT
```

---

### 10. Position Management

Query user liquidity positions.

List all positions for an owner:

```bash
sun --json position list --owner TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW
```

Filter by protocol:

```bash
sun --json position list --owner TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW --protocol V3
```

Pool tick info:

```bash
sun --json position tick TSUUVjysXV8YqHytSNjfkNXnnB49QDvZpx
```

---

### 11. Pair Info

Resolve trading pair information.

> **WARNING:** `pair info --token` **only accepts contract addresses**. Passing a symbol
> (e.g. `USDT`) will fail with an API error or return unexpected results.
> Always resolve the symbol to a contract address first using the
> [Supported Token Symbols](#supported-token-symbols) table or `token search`.

Query by USDT contract address:

```bash
sun --json pair info --token TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t
```

Query by WTRX contract address:

```bash
sun --json pair info --token T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb
```

---

### 12. Protocol Analytics

Fetch protocol-level metrics.

```bash
sun --json protocol info
```

```bash
sun --json protocol vol-history --start 2026-01-01 --end 2026-03-15
```

```bash
sun --json protocol users-history --start 2026-01-01 --end 2026-03-15
```

```bash
sun --json protocol tx-history --start 2026-01-01 --end 2026-03-15
```

```bash
sun --json protocol pools-history --start 2026-01-01 --end 2026-03-15
```

```bash
sun --json protocol liq-history --start 2026-01-01 --end 2026-03-15
```

---

### 13. Farm

Inspect SUN.IO farms.

```bash
sun --json farm list
```

Farm transactions for a specific owner:

```bash
sun --json farm tx --owner TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW --type stake
```

User farm positions:

```bash
sun --json farm positions --owner TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW
```

---

### 14. Transaction Scan

Scan DEX transaction activity.

> **IMPORTANT:** `--type` must be exactly one of: `swap`, `add`, `withdraw`.
> Invalid types return empty results instead of an error.

```bash
sun --json tx scan --type swap --token TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t --start 2026-01-01 --end 2026-03-15
```

```bash
sun --json tx scan --type add --start 2026-01-01 --end 2026-03-15
```

```bash
sun --json tx scan --type withdraw --start 2026-01-01 --end 2026-03-15
```

---

### 15. Generic Contract Calls

Read or send arbitrary TRON contract calls when higher-level commands are insufficient.

Read a contract (no wallet needed):

```bash
sun --json contract read TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t name
```

```bash
sun --json contract read TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t balanceOf --args '["TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW"]'
```

Send a contract call (requires wallet, use `--dry-run` to simulate):

```bash
sun --json --yes --dry-run contract send TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t approve --args '["TKzxdSv2FZKQrEqkKVgp5DcwEXBEKMg2Ax","1000000"]' --value 0
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
```

```bash
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
> balances, validate fee tiers, or reject invalid parameters.

Check balance first:

```bash
sun --json wallet balances
```

Simulate (preview transaction structure):

```bash
sun --json --yes --dry-run swap TRX USDT 100000000
```

Execute after reviewing dry-run result and confirming balance:

```bash
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
```

```bash
sun --json pool search "TRX USDT"
```

Verify balance is sufficient for both amount0 and amount1.

**Step 3 — Dry-run mint (preview only, does not validate balances or parameters):**

```bash
sun --json --yes --dry-run liquidity v3:mint --token0 TRX --token1 USDT --fee 3000 --tick-lower -887220 --tick-upper 887220 --amount0 1000000
```

**Step 4 — Execute after user confirms:**

```bash
sun --json --yes liquidity v3:mint --token0 TRX --token1 USDT --fee 3000 --tick-lower -887220 --tick-upper 887220 --amount0 1000000
```

---

### Pattern 4: Information Gathering

**Best for:** Answering user questions about tokens, pools, prices.

Query token price:

```bash
sun --json price TRX
```

Top APY pools:

```bash
sun --json pool top-apy --page-size 10
```

User positions:

```bash
sun --json position list --owner TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW
```

Pair info (requires contract address, not symbol):

```bash
sun --json pair info --token TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t
```

Limit output fields to reduce response size:

```bash
sun --json --fields address,network wallet address
```

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

**FORBIDDEN:** private keys, seed phrases, mnemonics, environment variable values containing secrets, agent wallet passwords.

**ALLOWED:** public wallet addresses, transaction hashes, token balances and prices.

To verify no secrets leak in output:

```bash
sun --json wallet address
```

The output must not contain private key material.

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
```

```bash
sun --json swap:quote TRX USDT 1000000000
```

Always check balance and get a quote before executing. `--dry-run` only shows transaction structure and does NOT validate balances or parameters.

### CRITICAL: Always Preview Before Write Operations

The AI agent **must never** execute a write operation (`swap`, `liquidity add/remove/mint`, `contract send`) without first showing the user a preview. The correct sequence is:

1. **Get a quote or dry-run** to show what will happen
2. **Display the preview** to the user (amounts, route, price impact, fees)
3. **Ask for explicit confirmation** from the user
4. **Only then** execute with `--yes`

> **WARNING:** Do not pass `--yes` on the first call. Use `--yes` only after the user
> has reviewed a preview and confirmed. Skipping the preview violates the security protocol.

**Correct pattern:**

```bash
sun --json swap:quote TRX USDT 100000000
```

Show results to user. After user confirms:

```bash
sun --json --yes swap TRX USDT 100000000
```

**For high-value operations (large amounts):** Always use `--dry-run` first in addition to the quote:

```bash
sun --json --yes --dry-run swap TRX USDT 1000000000
```

Then execute only after user reviews both the quote and the dry-run result.

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
| `pair info --token` needs address | `pair info` | Symbols cause API error or bad results | Use contract addresses, not symbols |
| `--tokens` filter needs addresses | `wallet balances` | Symbols like `TRX,USDT` cause `Invalid contract address provided` | Resolve symbols to addresses before calling |
| BigInt serialization in JSON output | `contract read` | Functions returning large integers (e.g. `totalSupply`) may crash with `Do not know how to serialize a BigInt` | Wrap result with `.toString()` client-side, or avoid `--json` for these calls |
| V3 invalid `--token-id` error misleading | `v3:increase`, `v3:decrease`, `v3:collect` | Non-existent token-id may report "amount required" instead of "position not found" | Verify the token-id exists via `position list` before operating |
| `AGENT_WALLET_PASSWORD` needs wallet store | `wallet address` | Fails if `~/.agent-wallet` directory is not initialized | Use `TRON_PRIVATE_KEY` or `TRON_MNEMONIC` instead, or initialize wallet store first |
| Testnet transactions need bandwidth/energy | All write commands on nile/shasta | Real execution may fail with resource errors even if dry-run succeeds | Ensure test wallet has sufficient TRX staked for bandwidth and energy |

---

## Troubleshooting

### "sun: command not found"
```bash
npm install -g @bankofai/sun-cli
```

### "Wallet not configured"
Set one of: `TRON_PRIVATE_KEY`, `TRON_MNEMONIC`, or `AGENT_WALLET_PASSWORD`.

> **NOTE on AGENT_WALLET_PASSWORD:** This mode requires an initialized wallet store
> at `~/.agent-wallet`. If the directory does not exist, the CLI will fail with
> `Secrets directory not found`. Use `TRON_PRIVATE_KEY` or `TRON_MNEMONIC` for
> simpler setup. Only set one wallet source at a time.

### "Network error" or "Timeout"
- Check internet connectivity
- For mainnet, set `TRONGRID_API_KEY`
- Retry (network may be congested)

### Transaction fails
- Ensure sufficient TRX for gas (100+ TRX recommended)
- Increase slippage: `--slippage 0.01`
- Verify token balance with `sun --json wallet balances`

### Testnet transaction fails with bandwidth/energy error
- Nile and Shasta testnets require staked TRX for bandwidth and energy
- Dry-run may succeed but real execution fails if the wallet lacks resources
- Fund the test wallet with testnet TRX and stake for resources before testing
- Use `--dry-run` to verify transaction structure even when resources are insufficient

---

**Version**: 3.2.0 (sun-cli based)
**Last Updated**: 2026-03-20
**Maintainer**: Bank of AI Team
