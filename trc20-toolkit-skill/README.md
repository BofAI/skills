# TRC20 Token Toolkit

> Universal TRC20 token operations for AI agents on TRON.

## Scripts

- `info.js` — Token metadata (name, symbol, decimals, totalSupply)
- `balance.js` — Single or batch balance queries with per-token error reporting in batch mode
- `transfer.js` — Transfer tokens with dry-run support and stricter address/amount validation
- `approve.js` — Set or check allowances with stricter address/amount validation

## Quick Start

```bash
cd trc20-toolkit-skill && npm install
export TRON_PRIVATE_KEY="<key>"

node scripts/info.js USDT
node scripts/balance.js --batch USDT,USDD,SUN
node scripts/transfer.js USDT TRecipient 10 --dry-run
node scripts/approve.js USDT TSpender 1000
```

## Validation Notes

- `balance.js --batch` now returns partial results when one or more token symbols are invalid.
- `transfer.js` rejects invalid recipient addresses and zero-value amounts before dry-run or broadcast.
- `approve.js` rejects invalid spender addresses and zero-value amounts before dry-run or broadcast.
- Multi-permission wallets may still require explicit `permissionId` handling outside the current script surface.

## Dependencies

- Node.js 18+
- [tronweb](https://www.npmjs.com/package/tronweb) ^6.0.0
