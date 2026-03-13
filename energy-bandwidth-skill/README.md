# Energy & Bandwidth Manager

> Monitor and manage TRON's Energy and Bandwidth resource system.

## Scripts

- `status.js` — Resource balances (energy, bandwidth, frozen TRX, pending unstakes)
- `estimate.js` — Estimate energy cost for a contract call
- `stake.js` — Stake TRX for Energy or Bandwidth
- `unstake.js` — Begin unstake (14-day cooldown) or withdraw expired
- `delegate.js` — Delegate/undelegate resources to other accounts

## Quick Start

```bash
cd energy-bandwidth && npm install
export TRON_PRIVATE_KEY="<key>"

node scripts/status.js
node scripts/stake.js 100 ENERGY --dry-run
```

## Dependencies

- Node.js 18+
- [tronweb](https://www.npmjs.com/package/tronweb) ^6.0.0
