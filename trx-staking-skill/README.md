# TRX Staking & SR Voting

> Stake TRX, vote for Super Representatives, and claim voting rewards on TRON.

## Scripts

- `status.js` — Staking overview (frozen TRX, TRON Power, votes, pending rewards)
- `sr-list.js` — List Super Representatives with vote counts
- `vote.js` — Vote for SRs (single or split across multiple)
- `rewards.js` — Check and claim voting rewards

## Quick Start

```bash
cd trx-staking && npm install
export TRON_PRIVATE_KEY="<key>"

node scripts/status.js
node scripts/sr-list.js --top 10
node scripts/vote.js TSRAddress --dry-run
node scripts/rewards.js
```

## Dependencies

- Node.js 18+
- [tronweb](https://www.npmjs.com/package/tronweb) ^6.0.0
