# TRC20 Token Toolkit

> Universal TRC20 token operations for AI agents on TRON.

## Scripts

- `info.js` — Token metadata (name, symbol, decimals, totalSupply)
- `balance.js` — Single or batch balance queries
- `transfer.js` — Transfer tokens with dry-run support
- `approve.js` — Set or check allowances

## Quick Start

```bash
cd trc20-toolkit && npm install
export TRON_PRIVATE_KEY="<key>"

node scripts/info.js USDT
node scripts/balance.js --batch USDT,USDD,SUN
node scripts/transfer.js USDT TRecipient 10 --dry-run
node scripts/approve.js USDT TSpender 1000
```

## Dependencies

- Node.js 18+
- [tronweb](https://www.npmjs.com/package/tronweb) ^6.0.0
