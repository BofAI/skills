# JustLend DAO

> Supply and borrow assets on TRON's largest lending protocol.

## Scripts

- `markets.js` — List markets with supply/borrow APY rates
- `position.js` — Check supplied/borrowed amounts, health factor, and liquidation risk
- `supply.js` — Supply assets to earn interest
- `withdraw.js` — Withdraw supplied assets
- `borrow.js` — Borrow against collateral (with health factor safeguard)
- `repay.js` — Repay borrowed assets

## Network Support

**Mainnet only.** JustLend contract addresses and market configurations are defined for TRON Mainnet. Nile and Shasta testnets are not supported.

## Quick Start

```bash
cd justlend-skill && npm install
export TRON_PRIVATE_KEY="<key>"

node scripts/markets.js
node scripts/supply.js TRX 100 --dry-run
node scripts/position.js
```

## Health Factor Safeguard

Before every borrow, `borrow.js` estimates the post-borrow health factor using on-chain oracle prices. If the health factor would drop below the configured minimum (default: **1.2**), the borrow is blocked. Thresholds are configurable in `resources/justlend_contracts.json`.

| Health Factor | Result |
|---|---|
| ≥ 1.5 | Safe — no warnings |
| 1.2 – 1.5 | Warning emitted |
| < 1.2 | Borrow blocked |

## Dependencies

- Node.js 18+
- [tronweb](https://www.npmjs.com/package/tronweb) ^6.0.0
