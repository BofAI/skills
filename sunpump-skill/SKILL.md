---
name: SunPump Trading
description: Buy and sell meme tokens on SunPump, the TRON bonding-curve launchpad.
version: 1.0.0
dependencies:
  - node >= 18.0.0
  - tronweb
tags:
  - defi
  - meme
  - tron
  - sunpump
  - bonding-curve
---

# SunPump Trading Skill

Trade meme tokens on **SunPump** — the leading fair-launch bonding-curve platform on TRON. This skill lets AI agents check prices, buy tokens, sell tokens, and inspect balances using helper scripts that interact with the SunPump smart contract (`TTfvyrAz86hbZk5iDpKD78pqLGgi8C7AAw`).

> [!NOTE]
> SunPump tokens trade on a **bonding curve** until they reach ~$69,420 market cap, at which point they automatically migrate to SunSwap V2. This skill only handles bonding-curve trading. If a token has migrated, use the **SunSwap** skill instead.

---

## Quick Start

### Prerequisites

1. **Node.js 18+** and **npm** installed.
2. Install dependencies:
   ```bash
   cd sunpump-skill && npm install
   ```
3. Set environment variables:
   ```bash
   export TRON_PRIVATE_KEY="<your-private-key>"
   export TRON_NETWORK="mainnet"          # or "nile" for testnet
   export TRONGRID_API_KEY="<optional>"   # recommended for mainnet
   ```

> [!CAUTION]
> **Never display or log the private key.** Environment variables must be set by the user before invoking any script.

---

## Available Scripts

All scripts live in `sunpump-skill/scripts/` and output structured JSON to **stdout**. Human-readable progress messages go to **stderr**.

### 1. `balance.js` — Check Balances

| Parameter | Required | Description |
|---|---|---|
| `tokenAddress` | No | TRC20 token address. Omit to show TRX only. |
| `walletAddress` | No | Wallet to query. Defaults to configured wallet. |

```bash
# TRX balance only
node scripts/balance.js

# Token + TRX balance
node scripts/balance.js TTokenAddress123

# Token balance for a different wallet
node scripts/balance.js TTokenAddress123 TWalletAddress456
```

**Output fields:** `wallet`, `trx_balance`, `token_balance`, `sunpump_approved`

---

### 2. `price.js` — Token Price & Trade Estimates

| Parameter | Required | Description |
|---|---|---|
| `tokenAddress` | **Yes** | SunPump token address |
| `--buy <trxAmount>` | No | Estimate tokens received for a TRX amount |
| `--sell <tokenAmount>` | No | Estimate TRX received for selling tokens |

```bash
# Basic price and state
node scripts/price.js TTokenAddress123

# Price + buy estimate for 100 TRX
node scripts/price.js TTokenAddress123 --buy 100

# Price + sell estimate for 50000 tokens
node scripts/price.js TTokenAddress123 --sell 50000
```

**Output fields:** `price_trx`, `state`, `state_label`, `buy_estimate`, `sell_estimate`

---

### 3. `buy.js` — Purchase Tokens

| Parameter | Required | Description |
|---|---|---|
| `tokenAddress` | **Yes** | SunPump token address |
| `trxAmount` | **Yes** | TRX to spend (human-readable, e.g. `100`) |
| `--slippage <pct>` | No | Slippage tolerance (default: `5`%, range: `0.1`–`50`%) |
| `--dry-run` | No | Estimate only, do not send transaction |

```bash
# Dry run — estimate only
node scripts/buy.js TTokenAddress123 100 --dry-run

# Execute with default 5% slippage
node scripts/buy.js TTokenAddress123 100

# Execute with 10% slippage (for volatile tokens)
node scripts/buy.js TTokenAddress123 50 --slippage 10
```

**Output fields:** `expected_tokens`, `min_tokens_with_slippage`, `fee_trx`, `status`, `tx_id`

---

### 4. `sell.js` — Sell Tokens

| Parameter | Required | Description |
|---|---|---|
| `tokenAddress` | **Yes** | SunPump token address |
| `tokenAmount` | **Yes** | Tokens to sell (human-readable) or `all` |
| `--slippage <pct>` | No | Slippage tolerance (default: `5`%, range: `0.1`–`50`%) |
| `--dry-run` | No | Estimate only, do not send transaction |

```bash
# Dry run — estimate only
node scripts/sell.js TTokenAddress123 50000 --dry-run

# Sell specific amount
node scripts/sell.js TTokenAddress123 50000

# Sell entire balance with 10% slippage
node scripts/sell.js TTokenAddress123 all --slippage 10
```

**Output fields:** `expected_trx`, `min_trx_with_slippage`, `fee_trx`, `status`, `tx_id`, `approve_tx`

> [!NOTE]
> The sell script automatically handles TRC20 approval. If the SunPump contract is not yet approved to spend the token, the script sends an `approve` transaction first, then waits before executing the sale.

---

## Usage Patterns

### Pattern 1: Quick Quote (Recommended First Step)

Always show the user a price estimate before executing a trade.

```bash
node scripts/price.js TTokenAddress123 --buy 100
```

Then confirm with the user before proceeding to `buy.js`.

### Pattern 2: Two-Step Confirmation (Recommended for AI Agents)

1. **Estimate:**
   ```bash
   node scripts/buy.js TTokenAddress123 100 --dry-run
   ```
2. **Show the estimate to the user and ask for confirmation.**
3. **Execute:**
   ```bash
   node scripts/buy.js TTokenAddress123 100
   ```

### Pattern 3: Full Pre-Trade Checklist

1. Check balance:
   ```bash
   node scripts/balance.js
   ```
2. Get price and estimate:
   ```bash
   node scripts/price.js TTokenAddress123 --buy 100
   ```
3. Dry-run the trade:
   ```bash
   node scripts/buy.js TTokenAddress123 100 --dry-run
   ```
4. Confirm with user, then execute:
   ```bash
   node scripts/buy.js TTokenAddress123 100
   ```

---

## Recommended Workflow for AI Agents

When a user asks to trade on SunPump, follow this sequence:

1. **Confirm the token address.** Ask the user for the exact contract address if they only give a name or symbol.
2. **Check price and state** with `price.js`. If `state` is `1` (migrated), inform the user and suggest using the SunSwap skill.
3. **Show a quote** using `--dry-run` or `price.js --buy`/`--sell`. Present the expected amount, fee, and slippage to the user.
4. **Get explicit confirmation** before executing any transaction.
5. **Execute** the trade and report the transaction ID.
6. **Verify** the result by checking the balance after the trade.

---

## Slippage Tolerance Configuration

Slippage parameters are defined in `resources/sunpump_contracts.json` under the `slippage` key:

| Parameter | Value | Description |
|---|---|---|
| `default_percent` | `5` | Applied when `--slippage` is omitted |
| `min_percent` | `0.1` | Minimum allowed slippage — rejects values below this |
| `max_percent` | `50` | Maximum allowed slippage — rejects values above this |
| `warn_above_percent` | `10` | Slippage above this triggers a warning to stderr |

The `validateSlippage()` function in `utils.js` enforces these bounds. If a user-supplied slippage is outside `[min, max]`, the script exits with a structured error. If it exceeds `warn_above_percent`, a warning is logged but execution continues.

```bash
# Uses default 5% slippage
node scripts/buy.js TTokenAddress123 100

# Explicit 2% slippage
node scripts/buy.js TTokenAddress123 100 --slippage 2

# 15% slippage — logs a warning, but proceeds
node scripts/buy.js TTokenAddress123 100 --slippage 15

# 60% slippage — rejected (exceeds max_percent)
node scripts/buy.js TTokenAddress123 100 --slippage 60
```

---

## SunSwap V2 Migration Handling

When a token reaches the ~$69,420 market cap threshold, SunPump automatically migrates its liquidity to **SunSwap V2**. The bonding curve closes and all buy/sell scripts will stop working for that token.

All trading scripts (`buy.js`, `sell.js`) check `getTokenState()` before executing. If the token has migrated (state ≠ 0), the script exits with a structured error containing:

- **`migration.reason`** — why the bonding curve is closed
- **`migration.sunswap_router`** — the SunSwap V2 router address for the current network (if available)
- **`migration.action`** — directs the agent to use the SunSwap skill instead

`price.js` also reports migration status in its output when querying a migrated token, but does not exit with an error since it is a read-only query.

**Agent behavior:** When a migration error is received, the agent should inform the user that the token has graduated from SunPump and offer to trade it via the SunSwap skill instead. Do not retry with SunPump scripts.

---

## Security Rules

> [!CAUTION]
> These rules are mandatory and must never be bypassed.

1. **Never display private keys** in output or logs.
2. **Never execute a trade without user confirmation.** Always show the estimate first.
3. **Prevent duplicate transactions.** Do not retry a submitted transaction unless the user explicitly requests it.
4. **Validate token addresses.** Ensure the address is a valid TRON base58 address starting with `T`.
5. **Check token state before trading.** Only trade tokens in state `0` (bonding curve active). Direct the user to SunSwap for migrated tokens.
6. **Warn about high slippage.** If slippage exceeds 10%, warn the user about the risk before proceeding.
7. **Never send TRX to the SunPump contract directly.** Always use the `purchaseToken` function via the scripts.

---

## Script Output Format

All scripts follow the same output convention:

- **stdout** — Structured JSON (parsed by the agent)
- **stderr** — Human-readable log messages (shown to the user)

Example JSON output from `buy.js --dry-run`:

```json
{
  "action": "buy",
  "token": "TTokenAddress123",
  "trx_amount": "100",
  "expected_tokens": "1523456.789",
  "min_tokens_with_slippage": "1447283.949",
  "fee_trx": "1",
  "slippage_percent": 5,
  "dry_run": true,
  "status": "dry_run"
}
```

---

## SunPump Key Facts

| Property | Value |
|---|---|
| Launcher contract | `TTfvyrAz86hbZk5iDpKD78pqLGgi8C7AAw` |
| Trading fee | 1% on buys and sells |
| Token creation fee | 20 TRX |
| Token decimals | 18 (standard for SunPump meme tokens) |
| TRX decimals | 6 (1 TRX = 1,000,000 SUN) |
| Bonding curve cap | ~$69,420 market cap |
| Post-migration | Tokens move to SunSwap V2 with ~100k TRX liquidity |
| Network | TRON Mainnet / Nile Testnet |

---

## Common Issues

| Problem | Cause | Solution |
|---|---|---|
| `TRON_PRIVATE_KEY environment variable is required` | Env var not set | User must set `export TRON_PRIVATE_KEY="..."` |
| `Token has migrated to SunSwap` | Token completed bonding curve | Use the **SunSwap** skill for trading |
| `Transaction failed: OUT_OF_ENERGY` | Insufficient energy/bandwidth | Stake TRX for Energy or ensure enough TRX for bandwidth |
| `Approval failed` | Token contract rejected approve | Check if the token address is correct |
| `Cannot find module 'tronweb'` | Dependencies not installed | Run `npm install` in the sunpump-skill directory |
| Unexpectedly low token amount | High slippage or price movement | Use `--dry-run` first; increase slippage if needed |

---

## User Communication Protocol

### Before Trade
> "I'll check the current price of token `<address>` on SunPump and show you an estimate before executing anything."

### Showing Quote
> "Here's the estimate for buying with **X TRX**:
> - Expected tokens: **Y**
> - Fee: **Z TRX** (1%)
> - Slippage protection: **W%**
>
> Shall I proceed with this trade?"

### After Trade
> "Transaction submitted! TX ID: `<txid>`
> You can verify it on [Tronscan](https://tronscan.org/#/transaction/<txid>).
> Let me check your updated balance..."

### On Error
> "The transaction failed: `<error message>`. This might be due to `<likely cause>`. Would you like me to try again with different parameters?"

---

## Resources

- **Contract config:** `resources/sunpump_contracts.json` — addresses, ABIs, and notes
- **SunPump platform:** https://sunpump.meme
- **SUN.io developer docs:** https://docs.sun.io/DEVELOPERS/Sunpump/SunpumpFunctions
- **Tronscan explorer:** https://tronscan.org

---

## Troubleshooting

### Module installation
```bash
cd sunpump-skill && npm install
```

### Network errors
- Check that `TRON_NETWORK` is set correctly (`mainnet` or `nile`).
- If rate-limited, set `TRONGRID_API_KEY`.

### Transaction failures
- Ensure sufficient TRX balance for trade amount + gas.
- For sells, the script handles approval automatically. If approval fails, check the token address.
- Use `--dry-run` to verify parameters before executing.

### Self-transfer validation
- The scripts will reject attempts to send tokens to yourself.
- If you need to move tokens between your own wallets, use a direct TRC20 transfer instead.

---

*Version 1.0.0 — Created by [M2M Agent Registry](https://m2mregistry.io) for Bank of AI*
