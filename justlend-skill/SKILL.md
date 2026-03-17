---
name: JustLend DAO
description: Supply and borrow assets on JustLend, TRON's largest lending protocol.
version: 1.0.0
dependencies:
  - node >= 18.0.0
  - tronweb
tags:
  - defi
  - lending
  - tron
  - justlend
  - yield
---

# JustLend DAO

Supply assets to earn interest and borrow against collateral on **JustLend DAO** — TRON's largest lending protocol ($5.95B TVL). Supports TRX, USDT, USDC, USDD, SUN, BTT, JST, WIN, and BTC markets.

---

## Quick Start

```bash
cd justlend-skill && npm install
export TRON_PRIVATE_KEY="<your-private-key>"
export TRON_NETWORK="mainnet"
```

> [!CAUTION]
> **Never display or log the private key.**

---

## Available Scripts

### 1. `markets.js` — List Markets with APY

```bash
node scripts/markets.js
```

**Output:** `markets[]` (symbol, jToken, supply_apy, borrow_apy)

### 2. `position.js` — Check Positions & Health Factor

```bash
node scripts/position.js
node scripts/position.js TWalletAddress
```

**Output:** `liquidity` (excess_liquidity_usd, shortfall_usd), `health_factor` (health_factor, total_borrow_usd), `positions[]` (supplied, borrowed)

### 3. `supply.js` — Supply Assets

```bash
node scripts/supply.js TRX 100 --dry-run
node scripts/supply.js USDT 50
```

> [!NOTE]
> For TRC20 tokens, the script auto-handles approval. For TRX, it uses the native payable mint.

### 4. `withdraw.js` — Withdraw Supplied Assets

```bash
node scripts/withdraw.js USDT 25 --dry-run
node scripts/withdraw.js TRX all
```

### 5. `borrow.js` — Borrow Against Collateral

```bash
node scripts/borrow.js USDT 100 --dry-run
node scripts/borrow.js USDT 100
```

> [!WARNING]
> Borrowing creates a debt position. If your collateral value drops below the required threshold, your position may be **liquidated**. The script automatically estimates the post-borrow health factor and blocks the transaction if it would fall below the safety threshold (default: 1.2).

### 6. `repay.js` — Repay Borrowed Assets

```bash
node scripts/repay.js USDT 50 --dry-run
node scripts/repay.js USDT all
```

---

## Usage Patterns

### Earn Yield (Supply Only)

```bash
node scripts/markets.js                     # Check APYs
node scripts/supply.js USDT 1000 --dry-run   # Estimate
node scripts/supply.js USDT 1000             # Execute
node scripts/position.js                     # Verify
```

### Borrow Against Collateral

```bash
node scripts/supply.js TRX 5000             # Supply collateral
node scripts/position.js                     # Check liquidity & health factor
node scripts/borrow.js USDT 100 --dry-run    # Estimate borrow (includes health factor projection)
node scripts/borrow.js USDT 100              # Execute (blocked if health factor < 1.2)
```

### Repay and Withdraw

```bash
node scripts/repay.js USDT all               # Repay full debt
node scripts/withdraw.js TRX all             # Withdraw collateral
```

---

## Supported Markets

| Asset | jToken | Decimals |
|---|---|---|
| TRX | `TE2RzoSV3wFK99w6J9UnnZ4vLfXYoxvRwP` | 6 |
| USDT | `TXJgMdjVX5dKiQaUi9QobwNxtSQaFqccvd` | 6 |
| USDC | `TNSBA6KvSvMoTqQcEgpVK7VhHT3z7wifxy` | 6 |
| USDD | `TKFRELGGoRgiayhwJTNNLqCNjFoLBh3Mnf` | 18 |
| SUN | `TGBr8uh9jBVHJhhkwSJvQN2ZAKzVkxDmno` | 18 |
| BTT | `TUaUHU9Dy8x5yNi1pKnFYqHWojot61Jfto` | 18 |
| JST | `TWQhCXaWz4eHK4Kd1ErSDHjMFPoPc9czts` | 18 |
| WIN | `TRg6MnpsFXc82ymUPgf5qbj59ibxiEDWvv` | 6 |
| BTC | `TLeEu311Cbw63BcmMHDgDLu7fnk9fqGcqT` | 8 |

---

## Health Factor Monitoring

The **health factor** measures how close a position is to liquidation:

```
Health Factor = Total Collateral Value (USD, adjusted by collateral factors) / Total Borrow Value (USD)
```

| Health Factor | Status | Action |
|---|---|---|
| > 1.5 | Safe | No action needed |
| 1.2 – 1.5 | Warning | Script logs a warning; consider reducing borrow or adding collateral |
| < 1.2 | Blocked | `borrow.js` refuses to execute — too close to liquidation |
| < 1.0 | Liquidatable | Position can be liquidated by anyone |

### Configuration

Thresholds are defined in `resources/justlend_contracts.json` under the `health_factor` key:

| Parameter | Default | Description |
|---|---|---|
| `min_threshold` | `1.2` | Borrows below this are blocked |
| `warn_threshold` | `1.5` | Borrows below this emit a warning |

### How It Works

1. **Before every borrow**, `borrow.js` calls `estimateHealthFactorAfterBorrow()` which:
   - Reads current account liquidity from the Comptroller (`getAccountLiquidity`)
   - Fetches the oracle price for the borrow asset (`getUnderlyingPrice`)
   - Computes total existing borrows in USD across all markets
   - Calculates the projected health factor after adding the new borrow
   - Blocks the transaction if the result is below `min_threshold`

2. **`position.js`** includes the current health factor in its output via `getHealthFactor()`, with warnings when it drops below safe levels.

3. **Dry-run mode** also estimates the health factor, so agents can preview the impact before committing.

### Example: Borrow Blocked by Health Factor

```bash
$ node scripts/borrow.js USDT 5000 --dry-run
```
```json
{
  "error": "Health factor safeguard: Borrowing 5000 USDT would result in a health factor of 1.08, which is below the minimum threshold of 1.2. Reduce the borrow amount or supply more collateral.",
  "estimated_health_factor": 1.08,
  "min_threshold": 1.2
}
```

---

## Security Rules

1. **Never display private keys.**
2. **Always dry-run before supplying or borrowing.**
3. **Check position health before borrowing.** Monitor `health_factor` in `position.js` output — if it approaches 1.0, liquidation is imminent.
4. **Repay borrows before withdrawing collateral** to avoid liquidation.
5. **Warn about liquidation risk** whenever a user borrows or the health factor is low.
6. **Never bypass the health factor safeguard.** If `borrow.js` blocks a transaction due to low health factor, do not attempt to call the contract directly.

---

## Common Issues

| Problem | Solution |
|---|---|
| `Unknown asset` | Use symbol from supported markets table |
| `No jTokens to redeem` | Nothing is supplied in that market |
| Supply fails for TRC20 | Approval may have failed — check allowance |
| Borrow fails | Insufficient collateral — supply more first |
| `redeemUnderlying` fails | Trying to withdraw more than supplied |

---

*Version 1.0.0 — Created by [M2M Agent Registry](https://m2mregistry.io) for Bank of AI*
