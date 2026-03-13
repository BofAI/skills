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

Supply assets to earn interest and borrow against collateral on **JustLend DAO** — TRON's largest lending protocol ($5.95B TVL). Supports TRX, USDT, USDC, USDD, SUN, BTT, and JST markets.

---

## Quick Start

```bash
cd justlend && npm install
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

### 2. `position.js` — Check Positions

```bash
node scripts/position.js
node scripts/position.js TWalletAddress
```

**Output:** `liquidity` (excess_liquidity_usd, shortfall_usd), `positions[]` (supplied, borrowed)

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
> Borrowing creates a debt position. If your collateral value drops below the required threshold, your position may be **liquidated**. Always check `position.js` for health before borrowing.

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
node scripts/position.js                     # Check liquidity
node scripts/borrow.js USDT 100 --dry-run    # Estimate borrow
node scripts/borrow.js USDT 100              # Execute
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
| TRX | `TLeEu311Vrv2asMEqrEAFRyAZGU83RB27h` | 6 |
| USDT | `TXJgMRrQHTzLMcKfSEZ4LRCWZkBq4iZ5EL` | 6 |
| USDC | `TX7kybeP6UwTBRHLNPYmswFESHfyjm9bAS` | 6 |
| USDD | `TX1x3z8wVJiSdVkFR2WdKtrqEQoRNYHoEW` | 18 |
| SUN | `TPYfcPk9T5C5fqwzAGdzYDCiWKJpGSoFma` | 18 |
| BTT | `TGkfRFBa3FKQP3YjibZL4kR1DuPcGS1eiS` | 18 |
| JST | `TRgRMmyNoelaqA7Md23hLKfnr1FEQoSHcH` | 18 |

---

## Security Rules

1. **Never display private keys.**
2. **Always dry-run before supplying or borrowing.**
3. **Check position health before borrowing.** Monitor `excess_liquidity_usd` — if it reaches 0, liquidation risk is imminent.
4. **Repay borrows before withdrawing collateral** to avoid liquidation.
5. **Warn about liquidation risk** whenever a user borrows or the health factor is low.

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
