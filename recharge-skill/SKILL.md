---
name: recharge-skill
description: Query B.AI credits, usage, and recharge orders, recharge an account, or reconcile an existing recharge through wallet-cli 4.14.0 bai commands. Use for BANK OF AI balance/order requests and stablecoin recharge requests.
version: 3.0.0
dependencies:
  - "@tron-walletcli/wallet-cli@4.14.0"
tags:
  - bankofai
  - balance
  - recharge
---

# B.AI Recharge

Use `wallet-cli bai`. Wallet-cli manages the account, API-key configuration, signing,
order creation, payment, and credit reporting. Do not introduce a separate wallet store,
configuration file, payment script, or recharge MCP client.

## Prerequisites

Require exactly `@tron-walletcli/wallet-cli@4.14.0`; verify with
`npm list --global --depth=0 --json @tron-walletcli/wallet-cli`.
Follow the [wallet-cli setup instructions](../wallet-cli/README.md),
[secret and authorization rules](../wallet-cli/references/safety.md), and
[machine interface](../wallet-cli/references/machine-interface.md).

Every `bai` command needs a B.AI API key configured through
`wallet-cli config baiApiKey --api-key-stdin -o json`. Feed the key directly from an approved,
non-logging secret source; do not request it in chat or read it back from configuration.
Saving the key does not validate it with B.AI. Queries and reporting need no wallet password;
recharge, including its preview, needs a configured wallet-cli account.

```bash
wallet-cli bai --json-schema -o json
wallet-cli bai recharge --json-schema -o json
wallet-cli bai report-recharge --json-schema -o json
```

Use `-o json` for operations. Handle a `command: "migration"` result before retrying the
original command under the shared rules; it is not evidence of a recharge.

## Read credits, usage, and orders

```bash
wallet-cli bai usage-summary -o json
wallet-cli bai usage-records --limit 20 -o json
wallet-cli bai recharge-orders --limit 20 -o json
```

Discover supported filters and pagination through each command's schema. Bound the number of
pages; do not expose account records beyond the user's request.

## Preview and recharge

Recharge is mainnet-only. Select the network explicitly:

| Network | Supported tokens |
| --- | --- |
| `tron:728126428` | USDT, USDD |
| `eip155:56` | USDT |
| `eip155:8453` | USDC |

USDT and USDC have a minimum recharge of 1. Preserve amount strings without floating-point
conversion. By default credits go to the owner of the API key; `--to` selects another B.AI
account by email or supported wallet address and requires an explicit user request.

```bash
wallet-cli bai recharge 1 --network tron:728126428 --token USDT --dry-run -o json
```

A preview checks the route and recipient, but creates no order, binds no address, and pays nothing.
Show the payer, recipient/recharge target, network, token, amount, fees, and `bindingRequired`.
If binding is required, explain that execution also signs B.AI's binding message and binds the
paying address to the API-key account. Obtain confirmation of the complete operation.

Run the confirmed command once without `--dry-run`, with `--password-stdin` connected to an
approved non-logging secret source. Do not split the flow into a separate manual payment.
For TRON GasFree, explicitly select `--scheme exact_gasfree` and a separate GasFree fee cap.

## Credit confirmation and recovery

- Inspect `creditStatus`, not only the exit code or `success`.
- `credited` means B.AI confirmed the credits. Report the actual transaction hash and target.
- `unconfirmed` means payment succeeded but credit confirmation is pending. Do not recharge
  again. Reconcile the original transaction using `wallet-cli bai report-recharge`.
- Reporting takes the original transaction hash and `--chain tron|bnb|base` (`bnb` for BSC),
  plus the original amount when available. A recharge to another person also needs both the
  original `--to` and `--target-id` from `rechargeTarget.confirmedTarget.targetId`.
- Reporting creates no order, signs nothing, and pays nothing. Repeated reporting of an already
  credited transaction does not add credits again. Bound retries and honor structured retry delays.
- On execution errors, inspect `error.code` and available payment details; reconcile ambiguous
  payment status before any new payment. Never parse error-message text to decide to retry.
- `bai_credentials_missing` requires local API-key setup; `bai_auth_failed` requires correcting
  that setup, not creating another order. Never print credentials when diagnosing either error.
