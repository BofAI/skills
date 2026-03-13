# JustLend DAO

> Supply and borrow assets on TRON's largest lending protocol.

## Scripts

- `markets.js` — List markets with supply/borrow APY rates
- `position.js` — Check supplied/borrowed amounts and health
- `supply.js` — Supply assets to earn interest
- `withdraw.js` — Withdraw supplied assets
- `borrow.js` — Borrow against collateral
- `repay.js` — Repay borrowed assets

## Quick Start

```bash
cd justlend && npm install
export TRON_PRIVATE_KEY="<key>"

node scripts/markets.js
node scripts/supply.js TRX 100 --dry-run
node scripts/position.js
```

## Dependencies

- Node.js 18+
- [tronweb](https://www.npmjs.com/package/tronweb) ^6.0.0
