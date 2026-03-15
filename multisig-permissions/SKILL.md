---
name: Multi-Sig & Account Permissions
description: Manage TRON multi-sig permissions — configure keys, thresholds, and co-signed proposals.
version: 1.0.0
dependencies:
  - node >= 18.0.0
  - tronweb
tags:
  - tron
  - security
  - multisig
  - permissions
  - account-management
---

# Multi-Sig & Account Permissions

Manage TRON's native three-tier permission model (Owner, Active, Witness) with built-in multi-sig support at the protocol level — no external contracts needed. Configure keys, thresholds, and operation scopes, then coordinate multi-signature transactions through a propose → approve → execute flow.

---

## Quick Start

```bash
cd multisig-permissions && npm install
export TRON_PRIVATE_KEY="<your-private-key>"
export TRON_NETWORK="mainnet"
```

> [!CAUTION]
> Misconfiguring **owner permissions** can permanently lock an account with no recovery. Always use `--dry-run` first and verify you control enough keys to meet the new threshold.

---

## Available Scripts

| Script | Purpose | Reads/Writes |
|--------|---------|-------------|
| `status.js` | View current permission configuration | Read-only |
| `update.js` | Modify account permissions (add/remove keys, thresholds, scope) | **Write** |
| `propose.js` | Create a multi-sig transaction proposal | **Write** |
| `approve.js` | Add your signature to a pending proposal | **Write** |
| `execute.js` | Broadcast a fully-signed transaction | **Write** |
| `pending.js` | List pending multi-sig proposals | Read-only |

---

## TRON Permission Model

Every TRON account has three permission tiers:

| Permission | Type | Purpose | Default |
|-----------|------|---------|---------|
| **Owner** | 0 | Full control. Only permission that can modify other permissions. | Account key, threshold 1 |
| **Active** | 2 | Day-to-day operations. Can be scoped to specific transaction types. | Account key, threshold 1, all ops |
| **Witness** | 1 | Block production (Super Representatives only). | Not set |

Each permission has **keys** (address + weight pairs) and a **threshold** (minimum total weight to authorize). Example: 3 keys with weight 1 each and threshold 2 = 2-of-3 multi-sig.

---

## Usage Patterns

### Pattern 1: Inspect Account Security

```bash
# Check your own account
node scripts/status.js

# Check any account
node scripts/status.js TXk8rQSAvPvBBNtqSoY3UkFdpMTMbqRMKU
```

### Pattern 2: Set Up Multi-Sig (2-of-3)

```bash
# Step 1: Preview changes (always dry-run first!)
node scripts/update.js add-key TKey2Address... --permission owner --weight 1 --dry-run
node scripts/update.js add-key TKey3Address... --permission owner --weight 1 --dry-run
node scripts/update.js set-threshold 2 --permission owner --dry-run

# Step 2: Or use a template for all at once
node scripts/update.js from-template basic-2of3 \
  --key1 TKey1... --key2 TKey2... --key3 TKey3... --dry-run

# Step 3: Execute when satisfied
node scripts/update.js from-template basic-2of3 \
  --key1 TKey1... --key2 TKey2... --key3 TKey3...
```

### Pattern 3: Restrict Agent to DeFi Only

```bash
# Agent key can only call smart contracts, humans retain 2-of-2 owner control
node scripts/update.js from-template agent-restricted \
  --key1 THumanKey... --key2 TBackupKey... --key3 TAgentKey... --dry-run
```

### Pattern 4: Multi-Sig Transaction Flow

```bash
# Signer 1: Propose a transfer
node scripts/propose.js transfer TRecipient... 10000 --memo "Q1 budget"

# Signer 2: Review and approve
node scripts/approve.js prop_1709312400_a3f2

# Any signer: Execute when threshold is met
node scripts/execute.js prop_1709312400_a3f2

# Check all pending proposals
node scripts/pending.js
```

### Pattern 5: Scope Active Permission Operations

```bash
# Restrict active permission to only TRX transfers and smart contract calls
node scripts/update.js scope-active --id 2 \
  --operations TransferContract,TriggerSmartContract --dry-run
```

---

## Permission Templates

| Template | Config | Description |
|----------|--------|-------------|
| `basic-2of3` | 2-of-3 owner, 1-of-1 active (all ops) | Standard multi-sig |
| `agent-restricted` | 2-of-2 owner (human+backup), 1-of-1 active (TriggerSmartContract only) | Agent can only call contracts |
| `team-tiered` | 3-of-5 owner, 2-of-3 active (transfers + contracts) | Team with tiered access |
| `weighted-authority` | Threshold 3: primary (weight 2) + two secondaries (weight 1) | Weighted key authority |

---

## Transaction Types (Operations)

Used with `scope-active --operations`:

| Operation | Description |
|-----------|-------------|
| `TransferContract` | Transfer TRX |
| `TransferAssetContract` | Transfer TRC10 tokens |
| `TriggerSmartContract` | Call any smart contract (DeFi, tokens, etc.) |
| `FreezeBalanceV2Contract` | Stake TRX for energy/bandwidth |
| `UnfreezeBalanceV2Contract` | Unstake TRX |
| `DelegateResourceContract` | Delegate energy/bandwidth |
| `VoteWitnessContract` | Vote for Super Representatives |
| `AccountPermissionUpdateContract` | Modify permissions (very dangerous in Active) |

See `resources/permission_config.json` for the full list.

---

## Security Rules

> [!WARNING]
> **Lockout prevention**: The `update.js` script refuses to execute if the new threshold exceeds the total key weight. However, you MUST verify you actually control the keys — the script cannot check this.

1. **Always dry-run first**: Every write operation supports `--dry-run`.
2. **Owner changes are irreversible**: Only the owner key set can modify permissions. If you lock yourself out, the account is permanently lost.
3. **Verify key control**: Before changing owner permissions, confirm you have access to enough keys to meet the new threshold.
4. **Scope active permissions**: Don't give agents all-operations access. Use `scope-active` to limit to `TriggerSmartContract`.
5. **Proposals expire**: Default expiry is 24 hours. Expired proposals cannot be executed.

---

## Multi-Sig Proposal Storage

Proposals are stored locally at `~/.clawdbot/multisig/pending/` as JSON files. After execution, they are archived to `~/.clawdbot/multisig/executed/`.

For multi-party setups, share the proposal ID with co-signers who have access to the same file system, or copy the proposal JSON file to them.

---

## Common Issues

### "LOCKOUT DANGER: threshold exceeds total key weight"
The script prevented a dangerous permission change. Reduce the threshold or add more keys.

### "Account not found or not activated"
The address has no on-chain account. Send at least 0.1 TRX to activate it.

### "Proposal has expired"
The proposal's 24-hour window has passed. Create a new proposal with `propose.js`.

### "Threshold not met"
The proposal needs more signatures. Check `pending.js` to see remaining weight needed.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TRON_PRIVATE_KEY` | Yes (write ops) | Private key for signing |
| `TRON_NETWORK` | No (default: mainnet) | `mainnet`, `nile`, or `shasta` |
| `TRONGRID_API_KEY` | No | TronGrid API key for higher rate limits |

---

*Version 1.0.0 — Created by [M2M Agent Registry](https://m2mregistry.io) for Bank of AI*
