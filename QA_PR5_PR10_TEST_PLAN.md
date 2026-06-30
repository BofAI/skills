# QA Test Plan for PR #5 and PR #10

This document gives QA a practical manual test plan for:

- PR `#5` `Add TRX Staking & SR Voting skill`
- PR `#10` `Add USDD / JUST Protocol skill`

Target repo:

- `git@github.com:BofAI/skills.git`

Target PRs:

- [PR #5](https://github.com/BofAI/skills/pull/5)
- [PR #10](https://github.com/BofAI/skills/pull/10)

## Scope

This plan covers:

- install/build sanity
- read-only script behavior
- safe dry-run behavior
- basic error handling

This plan does not require QA to perform irreversible production writes unless explicitly noted.

## General QA Rules

- Run each PR in a separate clean worktree or clone.
- Test on Node.js `20.x` or newer.
- Record command, exit code, stdout, stderr, and timestamp for every failure.
- When using TronGrid on mainnet, add a short delay between calls to reduce `429` rate-limit errors.
- If a step fails with `429`, retry once after `5-10` seconds before marking it failed.

## Environment Setup

### Common tools

- `git`
- `node`
- `npm`

### Recommended environment variables

For TRON mainnet tests:

```bash
export TRON_NETWORK=mainnet
export TRONGRID_API_KEY="<your-api-key>"
```

For write-path or dry-run tests that require a wallet context:

```bash
export TRON_PRIVATE_KEY="<qa-wallet-private-key>"
```

Use a dedicated QA wallet. Do not reuse a personal or production wallet.

## PR #5: TRX Staking & SR Voting

### Checkout

```bash
git fetch origin pull/5/head:pr-5
git switch pr-5
cd trx-staking-skill
```

### Install

```bash
npm ci
```

Expected:

- install completes successfully
- `package-lock.json` is consistent

### Syntax sanity

```bash
for f in scripts/*.js; do
  echo "CHECK $f"
  node --check "$f"
done
```

Expected:

- all files pass syntax check

### Test Case 5.1: List SRs

```bash
node scripts/sr-list.js --top 5
```

Expected:

- command exits `0`
- JSON output contains:
  - `total_witnesses`
  - `total_votes`
  - `super_representatives`
- `super_representatives` contains `5` entries
- each entry has `rank`, `address`, `vote_count`, `is_active_sr`

### Test Case 5.2: Wallet status with QA wallet

```bash
node scripts/status.js
```

Expected:

- command exits `0`
- JSON output contains:
  - `wallet`
  - `trx_balance`
  - `tron_power`
  - `votes`
  - `pending_reward_trx`

### Test Case 5.3: Wallet status by explicit address

```bash
node scripts/status.js <TRON_ADDRESS>
```

Expected:

- command exits `0`
- returns the requested wallet address in output

### Test Case 5.4: Rewards read path

```bash
node scripts/rewards.js
```

Expected:

- command exits `0`
- JSON output contains:
  - `wallet`
  - `pending_reward_trx`
  - `claimable`

### Test Case 5.5: Vote dry-run without TRON Power

Use a QA wallet with no staked TRX.

```bash
node scripts/vote.js <VALID_SR_ADDRESS> --dry-run
```

Expected:

- command exits non-zero
- error clearly states no TRON Power is available

### Test Case 5.6: Vote dry-run with invalid SR

Use a wallet that has TRON Power for this case if available.

```bash
node scripts/vote.js TPYmHEhy5n8TCEfYGqW2rPxsghSfzghPDn --dry-run
```

Expected:

- command exits non-zero
- output clearly says the address is not a registered witness/SR

### Optional Test Case 5.7: Vote dry-run with valid SR and funded staking wallet

Precondition:

- QA wallet has staked TRX and therefore non-zero TRON Power

Command:

```bash
node scripts/vote.js <VALID_SR_ADDRESS> --dry-run
```

Expected:

- command exits `0`
- output contains:
  - `action: "vote"`
  - `tron_power`
  - `votes`
  - `dry_run: true`
  - `status: "dry_run"`

### Pass Criteria for PR #5

- install succeeds
- read-only commands return structured JSON
- invalid or unsafe vote flows fail clearly
- dry-run path works when wallet preconditions are met

## PR #10: USDD / JUST Protocol

### Checkout

```bash
git fetch origin pull/10/head:pr-10
git switch pr-10
cd usdd-skill
```

### Install

```bash
npm ci
```

Expected:

- install completes successfully

### Syntax sanity

```bash
for f in scripts/*.js; do
  echo "CHECK $f"
  node --check "$f"
done
```

Expected:

- all files pass syntax check

### Test Case 10.1: PSM info read path

```bash
node scripts/psm-info.js
```

Expected:

- command exits `0`
- JSON output contains:
  - `network`
  - `psm.address`
  - `fees.tin`
  - `fees.tout`
  - `reserves.usdt_available`
  - `usdd.total_supply`

### Test Case 10.2: Balance lookup by address

```bash
node scripts/balance.js --address T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb
```

Expected:

- command exits `0`
- JSON output contains:
  - `wallet`
  - `network`
  - `balances`
- `balances` includes entries for `USDD`, `USDT`, `USDC`, `TRX`, and `JST`

### Test Case 10.3: Vault info read path

```bash
node scripts/vault-info.js --vault TRX-A
```

Expected:

- command exits `0`
- JSON output contains one vault entry with:
  - `name: "TRX-A"`
  - `collateral`
  - `total_debt_usdd`
  - `debt_ceiling_usdd`
  - `dust_usdd`

### Test Case 10.4: Invalid vault name

```bash
node scripts/vault-info.js --vault INVALID-A
```

Expected:

- command exits non-zero
- output clearly reports unknown vault

### Test Case 10.5: PSM dry-run with insufficient USDT

Use a QA wallet with zero or low USDT balance.

```bash
node scripts/psm-swap.js sell 1 --dry-run
```

Expected:

- command exits `0` or controlled non-zero depending on implementation path
- output must be structured JSON
- output must clearly state insufficient USDT balance
- no transaction is broadcast

### Optional Test Case 10.6: PSM sell dry-run with funded QA wallet

Precondition:

- QA wallet holds at least `1` USDT on TRON mainnet

Command:

```bash
node scripts/psm-swap.js sell 1 --dry-run
```

Expected:

- output contains:
  - `action: "psm_sell"`
  - `direction: "sell"`
  - `amount_usdt: "1"`
  - `dry_run: true`
  - `needs_approval`
- no transaction is broadcast

### Optional Test Case 10.7: PSM buy dry-run with funded QA wallet

Precondition:

- QA wallet holds enough USDD to buy `1` USDT

Command:

```bash
node scripts/psm-swap.js buy 1 --dry-run
```

Expected:

- output contains:
  - `action: "psm_buy"`
  - `direction: "buy"`
  - `amount_usdt: "1"`
  - `dry_run: true`
  - `needs_approval`
- no transaction is broadcast

### Optional Test Case 10.8: CDP lookup by ID

If QA has a known valid CDP ID:

```bash
node scripts/vault-info.js --cdp <CDP_ID>
```

Expected:

- command exits `0`
- output contains:
  - `cdp_id`
  - `owner`
  - `ilk`
  - `collateral_locked`
  - `actual_debt_usdd`
  - `collateralization_ratio`

### Pass Criteria for PR #10

- install succeeds
- read-only PSM and vault commands return structured JSON
- invalid vault input fails clearly
- dry-run swap path performs validation without broadcasting transactions

## Suggested QA Report Format

For each case, report:

- PR number
- test case ID
- environment
- command
- exit code
- actual result
- expected result
- pass/fail
- logs or screenshots if failed

Example:

```md
PR: #10
Case: 10.3
Env: mainnet, Node 20.19.5, TronGrid API key enabled
Command: node scripts/vault-info.js --vault TRX-A
Exit code: 0
Result: Returned vault object with debt ceiling and total debt fields
Status: PASS
```
