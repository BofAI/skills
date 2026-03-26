# PR2 Fix Verification Report

PR: `#2` Multi-Sig Permissions  
Verification date: `2026-03-26`  
Branch: `dev/readme-pr2`  
Network: `TRON Nile Testnet`

## Scope

This verification pass re-tested the issues previously identified in the PR2 QA report and validated the code changes made on `dev/readme-pr2`.

Covered in this pass:

- `D1`: active permission operation bitmask decoding / security analysis
- `D2`: `propose.js` support for `signer != controlled account`
- `D3`: owner multi-sig follow-up permission updates through the repository scripts
- `D4`: documentation alignment for the repaired signer / proposal / update flow
- post-update state synchronization behavior
- documentation alignment for the new proposal/update flow

## Code Changes Verified

- `multisig-permissions/scripts/utils.js`
- `multisig-permissions/scripts/status.js`
- `multisig-permissions/scripts/propose.js`
- `multisig-permissions/scripts/update.js`
- `multisig-permissions/SKILL.md`
- `multisig-permissions/README.md`
- `multisig-permissions/USE_CASES.md`

## Verification Summary

| Area | Result | Notes |
|---|---|---|
| D1: `TriggerSmartContract` bitmask decoding | Passed | `0000008000...` now decodes correctly |
| D1: security classification | Passed | restricted active permission no longer misclassified as all-ops |
| D2: active proposal for controlled account | Passed | `--account` correctly separates signer and controlled account |
| D2: active proposal execution | Passed | proposal executed on-chain with `Permission_id = 2` |
| D3: owner multi-sig permission update flow | Passed | `update.js` now creates a pending proposal instead of failing on single-sign broadcast |
| D3: owner proposal approval + execution | Passed | approval and execution completed successfully on-chain |
| D4: core documentation alignment | Passed | signer-role caveats, `--account`, and owner-proposal behavior are now documented |
| Post-update account state reads | Passed | scripts now use raw account reads and return updated permission state consistently in verification |

## Test Environment

### Controlled account under test

- Account: `TTGawBo54XV2St7vePhznv9Mkk8AXGfJ2R`
- Owner keys:
  - `TTGawBo54XV2St7vePhznv9Mkk8AXGfJ2R`
  - `TK7gemMcEaCpYR4MCVHDqgYuGh2uFuyRjb`
- Active agent key:
  - `TBQ6yWFthbEv2e9du6z5ceqAYZLwZeFEcJ`

### Nile contracts used

- USDT: `TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj`

## Detailed Results

### 1. D1 Verification: operation bitmask decoding

The account was configured with restricted active permissions and then re-read through the updated scripts.

Observed `status.js` output:

- owner: `2-of-2`
- active name: `agent-defi`
- operations:
  - `TriggerSmartContract`
- operations hex:
  - `0000008000000000000000000000000000000000000000000000000000000000`
- security level:
  - `strong`

After a follow-up scoped update, the same account was re-read again and correctly showed:

- operations:
  - `FreezeBalanceV2Contract`
  - `TriggerSmartContract`
- operations hex:
  - `0008008000000000000000000000000000000000000000000000000000000000`

Conclusion:

- `decodeOperations()` is now aligned with TRON's accepted bit ordering
- `classifySecurity()` no longer treats this restricted active scope as all-operations access

### 2. D2 Verification: controlled-account active proposal flow

Using the active agent key, a proposal was created against the controlled account with:

```bash
TRON_NETWORK=nile TRON_PRIVATE_KEY=<agent-key> \
node scripts/propose.js contract-call TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj \
  "approve(address,uint256)" '["TB1JKi9cPxrwy34n4iVYif8W7h9mfn9vXD","1"]' \
  --permission active \
  --account TTGawBo54XV2St7vePhznv9Mkk8AXGfJ2R
```

Observed proposal fields:

- `permission = active`
- `account = TTGawBo54XV2St7vePhznv9Mkk8AXGfJ2R`
- `signer = TBQ6yWFthbEv2e9du6z5ceqAYZLwZeFEcJ`
- `threshold = 1`

The proposal was then executed successfully:

- tx: `70a0a51d9c62e80d25f9a40ffad4d5ed361c814f9500bc249c8d99e724e9fb6b`
- chain result: `SUCCESS`
- contract type: `TriggerSmartContract`
- permission id: `2`

Conclusion:

- `propose.js` no longer forces the signer address to also be the controlled account
- the `agent-restricted` active path now works as intended

### 3. D3 Verification: owner multi-sig follow-up permission updates

After the account was already in owner multi-sig mode, a follow-up permission change was attempted:

```bash
TRON_NETWORK=nile TRON_PRIVATE_KEY=<owner-key-1> \
node scripts/update.js scope-active --id 2 \
  --operations TriggerSmartContract,FreezeBalanceV2Contract
```

New behavior:

- `update.js` did not attempt an unsafe single-sign broadcast
- it created a pending owner proposal instead

Observed output:

- `status = proposal_created`
- proposal id: `prop_1774492912_3f32`

The proposal was then approved and executed through the existing flow:

1. `approve.js prop_1774492912_3f32`
2. `execute.js prop_1774492912_3f32`

Successful execution tx:

- `08fcd1cc5c4f9ad2b1c12ccbffd90fecaf8f806175143298d8d301b7820eacce`

Conclusion:

- the repository scripts now support owner multi-sig follow-up permission changes through propose/approve/execute
- the previous single-sign failure mode is resolved for this path

### 4. Synchronization behavior

The updated code now uses raw account reads and adds post-update synchronization checks.

Observed result in this verification pass:

- updated account state was read back consistently after permission updates
- subsequent `status.js` and `propose.js` operations matched the live on-chain permission state used during testing

Conclusion:

- the previous stale-read behavior is materially reduced for the tested flows
- no false "old threshold" or "old active permission" state was observed in the final verification pass

### 5. D4 Verification: documentation alignment

The docs were re-checked against the repaired implementation and updated where earlier wording overstated or blurred the actual behavior.

Updated documentation areas:

- `SKILL.md`
- `README.md`
- `USE_CASES.md`

What was aligned:

- signer environment variables now explicitly state that the derived address, not the variable name, determines the effective owner / active role
- `propose.js --account` is documented for controlled-account active flows
- owner multi-sig permission changes are documented as proposal-based updates, not immediate one-step broadcasts
- use cases that previously implied broader multi-active-id routing support were narrowed to match the current script surface

Conclusion:

- the earlier documentation mismatch is no longer a blocking issue for the repaired PR2 flow
- remaining doc work is general polish rather than a known correctness gap

## Key On-Chain Records

| Purpose | Transaction | Result |
|---|---|---|
| Apply `agent-restricted` template | `438deea4e4ff3e264251e5a2c82e67f34068c8c80a4d5982da29749e6c25060c` | SUCCESS |
| Execute active proposal with `--account` | `70a0a51d9c62e80d25f9a40ffad4d5ed361c814f9500bc249c8d99e724e9fb6b` | SUCCESS |
| Execute owner multi-sig permission-update proposal | `08fcd1cc5c4f9ad2b1c12ccbffd90fecaf8f806175143298d8d301b7820eacce` | SUCCESS |

## Final Conclusion

The previously reported high-priority issues were successfully fixed and re-validated on Nile:

- `D1` fixed
- `D2` fixed
- `D3` fixed
- `D4` fixed at the core workflow/documentation level

The updated `multisig-permissions` implementation now supports:

- correct restricted active permission decoding
- correct controlled-account active proposal generation
- correct owner multi-sig follow-up permission updates through the repository workflow

Based on this verification pass, the repaired PR2 code is functionally working for the tested scenarios.
