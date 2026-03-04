---
name: Energy & Bandwidth Manager
description: Monitor and manage TRON's Energy and Bandwidth resource system — stake, unstake, delegate, and estimate costs.
version: 1.0.0
dependencies:
  - node >= 18.0.0
  - tronweb
tags:
  - tron
  - energy
  - bandwidth
  - staking
  - resources
---

# Energy & Bandwidth Manager

Manage TRON's unique resource system. Energy is consumed by smart contract execution; Bandwidth is consumed by transaction byte-size. Both are obtained by staking (freezing) TRX. This skill lets agents check resource balances, estimate costs, stake/unstake TRX for resources, and delegate resources to other accounts.

---

## Quick Start

```bash
cd energy-bandwidth && npm install
export TRON_PRIVATE_KEY="<your-private-key>"
export TRON_NETWORK="mainnet"
```

> [!CAUTION]
> **Never display or log the private key.**

---

## Available Scripts

### 1. `status.js` — Resource Overview

```bash
node scripts/status.js                    # Own wallet
node scripts/status.js TWalletAddress     # Specific wallet
```

**Output:** `energy` (available, limit, used, frozen_trx), `bandwidth` (available, limit, used, free_limit, frozen_trx), `pending_unstakes[]`

### 2. `estimate.js` — Estimate Energy Cost

```bash
node scripts/estimate.js <contractAddress> <functionSelector> [params] [callValue]
node scripts/estimate.js TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t "transfer(address,uint256)" "TRecipient,1000000"
```

**Output:** `estimated_energy`, `contract`, `function`

### 3. `stake.js` — Stake TRX for Resources

```bash
node scripts/stake.js 100 ENERGY --dry-run
node scripts/stake.js 50 BANDWIDTH
```

### 4. `unstake.js` — Unstake TRX (14-day Cooldown)

```bash
node scripts/unstake.js 50 ENERGY --dry-run       # Begin cooldown
node scripts/unstake.js --withdraw --dry-run       # Claim expired unstakes
```

> [!WARNING]
> Unstaking begins a **14-day cooldown**. During this period the TRX is locked and does not earn resources. After 14 days, use `--withdraw` to claim.

### 5. `delegate.js` — Delegate Resources

```bash
node scripts/delegate.js TRecipient 100 ENERGY --dry-run
node scripts/delegate.js --undelegate TRecipient 100 ENERGY --dry-run
```

---

## TRON Resource Key Facts

| Property | Value |
|---|---|
| Free bandwidth per day | 600 points |
| Energy source | Stake TRX for ENERGY |
| Bandwidth source | Stake TRX for BANDWIDTH + 600 free/day |
| Unstake cooldown | 14 days |
| Delegation | Can delegate to other accounts |

---

## Security Rules

1. **Never display private keys.**
2. **Always dry-run before staking/unstaking.** These operations lock TRX.
3. **Warn about the 14-day unstake cooldown.** Users must understand the lockup.
4. **Check resource status before operations** to avoid staking more than needed.

---

## Common Issues

| Problem | Solution |
|---|---|
| `Insufficient TRX` | Check balance with `status.js` first |
| `No expired unstakes` | Wait for the 14-day cooldown to complete |
| Energy estimate returns 0 | Function may be view-only (no energy needed) |

---

*Version 1.0.0 — Created by [M2M Agent Registry](https://m2mregistry.io) for Bank of AI*
