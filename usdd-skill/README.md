# USDD / JUST Protocol

> USDD stablecoin operations — PSM swaps, vault position queries, and balance checks via the JUST Protocol on TRON.

## Scripts

- `psm-swap.js` — Buy/sell USDT via PSM at 1:1 (zero fee)
- `psm-info.js` — PSM state: fees, USDT reserves, USDD supply
- `balance.js` — Check USDD, USDT, USDC, TRX, and JST balances
- `vault-info.js` — Vault (CDP) parameters and individual position queries

## Quick Start

```bash
cd usdd-skill && npm install
export TRON_PRIVATE_KEY="<key>"

node scripts/psm-info.js
node scripts/balance.js
node scripts/psm-swap.js sell 1000 --dry-run
node scripts/vault-info.js
```

## Dependencies

- Node.js 18+
- [tronweb](https://www.npmjs.com/package/tronweb) ^6.0.0
