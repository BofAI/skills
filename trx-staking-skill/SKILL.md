---
name: TRX Staking & SR Voting
description: Stake TRX, vote for Super Representatives, and claim voting rewards on TRON.
version: 1.0.0
dependencies:
  - node >= 18.0.0
  - tronweb
tags:
  - tron
  - staking
  - voting
  - governance
  - super-representative
---

# TRX Staking & SR Voting

Stake TRX to earn TRON Power, vote for Super Representatives (SRs), and claim voting rewards. TRON uses Delegated Proof of Stake — the top 27 SRs by vote count produce blocks and distribute rewards proportionally to voters every 6 hours.

---

## Quick Start

```bash
cd trx-staking && npm install
export TRON_PRIVATE_KEY="<your-private-key>"
export TRON_NETWORK="mainnet"
```

> [!CAUTION]
> **Never display or log the private key.**

---

## Available Scripts

### 1. `status.js` — Staking Overview

```bash
node scripts/status.js
node scripts/status.js TWalletAddress
```

**Output:** `tron_power`, `total_frozen_trx`, `votes[]`, `unused_tron_power`, `pending_reward_trx`

### 2. `sr-list.js` — List Super Representatives

```bash
node scripts/sr-list.js              # Top 27 (active SRs)
node scripts/sr-list.js --top 50     # Top 50 (includes partners)
```

**Output:** `super_representatives[]` (rank, address, url, vote_count, vote_share, is_active_sr)

### 3. `vote.js` — Vote for SRs

```bash
# All votes to one SR
node scripts/vote.js TSRAddress --dry-run
node scripts/vote.js TSRAddress

# Split votes across multiple SRs
node scripts/vote.js --split TSR1:60,TSR2:40 --dry-run
```

> [!NOTE]
> You must have TRON Power (staked TRX) before voting. Use the **energy-bandwidth** skill to stake TRX.

### 4. `rewards.js` — Voting Rewards

```bash
node scripts/rewards.js              # Check pending rewards
node scripts/rewards.js --claim --dry-run
node scripts/rewards.js --claim
```

---

## Usage Patterns

### Full Staking Workflow

1. **Stake TRX** (via energy-bandwidth skill): `node stake.js 1000 ENERGY`
2. **Check TRON Power**: `node scripts/status.js`
3. **Browse SRs**: `node scripts/sr-list.js --top 10`
4. **Vote**: `node scripts/vote.js TSRAddress --dry-run` → confirm → execute
5. **Check rewards periodically**: `node scripts/rewards.js`
6. **Claim**: `node scripts/rewards.js --claim`

---

## Key Facts

| Property | Value |
|---|---|
| 1 frozen TRX | = 1 TRON Power (TP) |
| Active SRs | Top 27 by votes |
| SR Partners | Ranks 28-127 |
| Vote cycle | Every 6 hours |
| Block reward | 128 TRX per cycle, proportional to votes |
| Unstake cooldown | 14 days |

---

## Security Rules

1. **Never display private keys.**
2. **Dry-run before voting.** Votes replace previous votes entirely.
3. **Verify SR addresses** before voting — confirm via `sr-list.js`.
4. **Understand that voting replaces all previous votes.** Each vote transaction sets the complete vote slate.

---

## Common Issues

| Problem | Solution |
|---|---|
| `No TRON Power` | Stake TRX first using energy-bandwidth skill |
| `Percentages don't sum to 100%` | Adjust split percentages |
| `No rewards to claim` | Wait for a vote cycle (6 hours) after voting |

---

*Version 1.0.0 — Created by [M2M Agent Registry](https://m2mregistry.io) for Bank of AI*
