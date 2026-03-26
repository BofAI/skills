# Multi-Sig & Account Permissions

🔐 Configure TRON's native account permission system and coordinate multi-signature transactions.

## Quick Start

```bash
cd multisig-permissions && npm install
export TRON_PRIVATE_KEY="<your-key>"
export TRON_NETWORK="mainnet"

# Check current permissions
node scripts/status.js

# Set up 2-of-3 multi-sig
node scripts/update.js from-template basic-2of3 \
  --key1 TKey1... --key2 TKey2... --key3 TKey3... --dry-run

# Multi-sig transaction flow
node scripts/propose.js transfer TRecipient... 10000 --memo "Payment"
node scripts/approve.js prop_xxxxx_xxxx
node scripts/execute.js prop_xxxxx_xxxx
```

## Scripts

- **status.js** — View account permission configuration and security analysis
- **update.js** — Modify permissions (add/remove keys, set thresholds, scope operations, apply templates)
- **propose.js** — Create multi-sig transaction proposals (TRX transfer, TRC20 transfer, contract call)
- **approve.js** — Add your signature to a pending proposal
- **execute.js** — Broadcast a fully-signed transaction to the network
- **pending.js** — List and filter pending multi-sig proposals
- **review.js** — Human CLI: list, inspect, co-sign, and execute proposals in one tool

## Templates

Keys are numbered positionally across all roles in the template (owner first, then active-only roles):

| Template | Key mapping | Description |
|----------|-------------|-------------|
| `basic-2of3` | `--key1`..`--key3` (owner keys) | Standard 2-of-3 multi-sig |
| `agent-restricted` | `--key1` HUMAN, `--key2` BACKUP (owner), `--key3` AGENT (active) | Agent limited to smart contract calls only |
| `team-tiered` | `--key1`..`--key5` (owner keys, first 3 reused in active) | 3-of-5 owner, 2-of-3 active for daily ops |
| `weighted-authority` | `--key1` PRIMARY (wt 2), `--key2`..`--key3` SECONDARY (wt 1) | Primary key has extra weight |

## Important: Wait for On-Chain Confirmation After Permission Updates

After running `update.js` to change account permissions, the new permission state is **not immediately available on-chain**. You must wait for the transaction to be confirmed and the node to reflect the updated state before creating proposals with `propose.js`.

**Before creating any proposal after a permission update:**

1. Run `node scripts/status.js` and verify the output shows the new keys, weights, and thresholds.
2. If `status.js` still shows the old permissions, wait 10–30 seconds and check again.
3. Only proceed with `propose.js` once `status.js` confirms the expected permission configuration.

Skipping this step can cause `propose.js` to build transactions against stale permission data (wrong threshold, missing signers), which will fail at execution time.

## Demo: Hybrid Signature Workflow (Human + Agent)

This walkthrough demonstrates a 2-of-2 multi-sig setup where **Key A** is held by a human and **Key B** is held by the agent. The agent initiates a TRX transfer proposal, and the human reviews and co-signs it before broadcast.

**Setup:** Account `TJf2n7Wq...` is configured with 2-of-2 owner permission:
- Key A (human): `THumanKey8xR2mVp...` (weight 1)
- Key B (agent): `TAgentKeyQ9nZw3...` (weight 1)
- Owner threshold: 2

---

### Step 1 — Agent proposes a transfer

The agent builds the transaction and signs it with Key B.

```bash
# Agent's environment
$ export TRON_PRIVATE_KEY="<agent-private-key>"
$ node scripts/propose.js transfer TRecipientAddr... 500 --memo "Q1 vendor payment"
```
```
Building transfer transaction (permission: owner, threshold: 2) ...
Signing with caller key ...
Proposal saved to ~/.clawdbot/multisig/pending/prop_1710345600_b7e4.json
```
```json
{
  "proposalId": "prop_1710345600_b7e4",
  "description": "Transfer 500 TRX to TRecipientAddr...",
  "memo": "Q1 vendor payment",
  "permission": "owner",
  "threshold": 2,
  "signatures": {
    "collected": 1,
    "collected_weight": 1,
    "required_weight": 2,
    "threshold_met": false
  },
  "expires": "2026-03-14T12:00:00.000Z",
  "saved_to": "~/.clawdbot/multisig/pending/prop_1710345600_b7e4.json",
  "next_step": "Share proposal ID with co-signers: node approve.js prop_1710345600_b7e4"
}
```

The agent shares `prop_1710345600_b7e4` with the human for review.

---

### Step 2 — Human reviews the pending proposal

The human inspects the proposal before signing.

```bash
# Human's environment (no private key needed for read-only review)
$ node scripts/review.js
```
```
Found 1 pending proposal(s):

  [AWAITING] prop_1710345600_b7e4
    Transfer 500 TRX to TRecipientAddr...
    Signatures: 1/2 | Time left: 23h 58m
    -> Review:  node review.js prop_1710345600_b7e4 --sign
```

```bash
# Inspect details (still no key needed)
$ node scripts/review.js prop_1710345600_b7e4
```
```
=== PROPOSAL DETAILS ===

  ID:          prop_1710345600_b7e4
  Description: Transfer 500 TRX to TRecipientAddr...
  Memo:        Q1 vendor payment
  Permission:  owner (id=0)
  Created:     2026-03-13T12:00:00.000Z
  Expires:     2026-03-14T12:00:00.000Z (23h 58m)

--- Signatures ---
  Threshold:   2 (weight required)
  Collected:   1/2 weight from 1 signer(s)
  Status:      AWAITING SIGNATURES

  Signers so far:
    - TAgentKeyQ9nZw3... (weight 1)

  All authorized keys:
    - THumanKey8xR2mVp... (weight 1) [pending]
    - TAgentKeyQ9nZw3... (weight 1) [SIGNED]
```

The human verifies: correct recipient, correct amount, correct memo.

---

### Step 3 — Human co-signs the proposal

```bash
$ export TRON_HUMAN_PRIVATE_KEY="<human-private-key>"
$ node scripts/review.js prop_1710345600_b7e4 --sign
```
```
=== PROPOSAL DETAILS ===
  ...
Signing proposal with THumanKey8xR2mVp... ...
Signature added (weight 1). Total weight: 2/2
```
```json
{
  "proposalId": "prop_1710345600_b7e4",
  "action": "signed",
  "signer": "THumanKey8xR2mVp...",
  "signatures": {
    "collected": 2,
    "collected_weight": 2,
    "required_weight": 2,
    "threshold_met": true
  },
  "next_step": "Ready! Execute: node review.js prop_1710345600_b7e4 --sign --execute"
}
```

---

### Step 4 — Either party executes (broadcasts) the transaction

```bash
$ node scripts/review.js prop_1710345600_b7e4 --sign --execute
```
```
Broadcasting transaction ...
Transaction submitted: 9c4a2f8e1d3b5a7096e8f2c4d6a8b0e2...abcdef1234567890
Proposal archived to ~/.clawdbot/multisig/executed/prop_1710345600_b7e4.json
```
```json
{
  "proposalId": "prop_1710345600_b7e4",
  "action": "signed_and_executed",
  "signer": "THumanKey8xR2mVp...",
  "signatures": 2,
  "threshold": 2,
  "status": "submitted",
  "tx_id": "9c4a2f8e1d3b5a7096e8f2c4d6a8b0e2...abcdef1234567890",
  "archived_to": "~/.clawdbot/multisig/executed/prop_1710345600_b7e4.json"
}
```

---

### Step 5 — Verify no pending proposals remain

```bash
$ node scripts/review.js
```
```
No pending proposals.
The agent can create one with: node propose.js transfer <to> <amount>
```

### Summary

| Step | Actor | Script | What happens |
|------|-------|--------|-------------|
| 1 | Agent (Key B) | `propose.js` | Builds tx, signs with Key B, saves proposal |
| 2 | Human (Key A) | `review.js` | Reviews proposal details (no key needed) |
| 3 | Human (Key A) | `review.js --sign` | Co-signs with Key A, threshold met (2/2) |
| 4 | Either | `review.js --sign --execute` | Broadcasts fully-signed tx to TRON network |

## Dependencies

- Node.js >= 18.0.0
- tronweb ^6.0.0

## Version

1.0.0 (March 2026)

## License

MIT — see LICENSE for details.
