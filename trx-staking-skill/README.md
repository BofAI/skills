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

## Demo: Claim Rewards Flow

### Step 1 — Check pending rewards

```bash
$ node scripts/rewards.js
```
```json
{
  "wallet": "TJf2n7Wq3RbGvNqhPKdy8Y3THXWB4ctqLz",
  "pending_reward_trx": "12.450000",
  "pending_reward_raw": "12450000",
  "claimable": true
}
```

### Step 2 — Dry-run the claim

```bash
$ node scripts/rewards.js --claim --dry-run
```
```
Claiming 12.45 TRX in voting rewards ...
```
```json
{
  "action": "claim_rewards",
  "amount_trx": "12.450000",
  "dry_run": true,
  "status": "dry_run"
}
```

### Step 3 — Execute the claim

```bash
$ node scripts/rewards.js --claim
```
```
Claiming 12.45 TRX in voting rewards ...
```
```json
{
  "action": "claim_rewards",
  "amount_trx": "12.450000",
  "dry_run": false,
  "status": "submitted",
  "tx_id": "a1b2c3d4e5f6...7890abcdef1234567890abcdef1234567890abcdef"
}
```

### Step 4 — Verify rewards were claimed

```bash
$ node scripts/rewards.js
```
```json
{
  "wallet": "TJf2n7Wq3RbGvNqhPKdy8Y3THXWB4ctqLz",
  "pending_reward_trx": "0",
  "pending_reward_raw": "0",
  "claimable": false
}
```

## Dependencies

- Node.js 18+
- [tronweb](https://www.npmjs.com/package/tronweb) ^6.0.0
