# Machine Interface Contract

Use this reference when parsing results, handling errors, polling transactions, paginating, or
providing secrets non-interactively. It summarizes the stable `wallet-cli.result.v1` contract in
wallet-cli 4.16.0.

## Calling convention

```bash
wallet-cli <command> -o json [--network <id>] [--timeout <ms>] [--account <id|label>]
```

JSON mode writes exactly one terminal result object to stdout. Diagnostics go to stderr.

`--timeout` is one deadline for the whole command: node, service, and device calls, approvals,
Ledger confirmation, and waiting for confirmation (built-in 90000, which `config timeoutMs` can
change; `0` disables it). Time spent at an interactive TTY prompt does not count; reading a
`*-stdin` source does. No transaction or payment is submitted with less than 2000 ms left; that
step fails with `timeout`, and approvals sent before it stay on chain. `--wait-timeout` and the
`waitTimeoutMs` config key no longer exist.

## Network ids

Use canonical CAIP-2 ids for TRON chain operations:

| Network | Canonical id | Permanent input alias |
|---|---|---|
| Mainnet | `tron:728126428` | `tron:mainnet` |
| Nile | `tron:3448148188` | `tron:nile` |
| Shasta | `tron:2494104990` | `tron:shasta` |

Aliases are accepted only when selecting a network. `chain.network`, `networks` results, and
configuration keys report canonical ids, so never compare those fields with an alias.

## Startup wallet-data upgrades

Operational commands check the persisted wallet schema before executing the requested command.
`--help`, `--version`, `--json-schema`, and bare `wallet-cli` never read wallet data and skip this
check. When an upgrade runs, stdout still contains one valid result envelope, but its canonical command is
`migration` and `data.originalCommandExecuted` is `false`. The triggering command was not run.

- A successful upgrade reports `data.upgraded: true`. Inspect and report it, then reapply the
  authorization and confirmation rules before invoking the original command once. Obtain a new
  mainnet or high-risk confirmation if migration occurred after the earlier confirmation.
- An interactive cancellation reports exit `0`, `data.upgraded: false`, and
  `data.cancelled: true`. Stop without retrying.
- A password-bearing migration without an approved password channel returns exit `2` with
  `error.code: "migration_required"`. Return control to the user or use an already approved
  `--password-stdin` source.
- Do not interpret the migration envelope using the triggering command's leaf schema.
- Discovery output is not an operational result envelope: root/group `--json-schema` returns a
  command catalog and leaf `--json-schema` returns its input schema. Do not require
  `wallet-cli.result.v1` when parsing discovery output.

## Exit codes

| Exit | Meaning | First response |
|---|---|---|
| `0` | The CLI completed the requested command | Inspect `success`, then command-specific state |
| `1` | Runtime, network, wallet, signing, or chain execution failure | Branch on `error.code`; reconcile ambiguous broadcasts |
| `2` | Malformed or invalid invocation | Correct flags/values using `--json-schema`; do not retry unchanged |

The exit-code class is the hard contract. Error-code values are extensible, so tolerate unknown
codes within the same exit class.

## Result envelope

Success:

```json
{
  "schema": "wallet-cli.result.v1",
  "success": true,
  "command": "account.balance",
  "data": {},
  "meta": { "durationMs": 42, "warnings": [] },
  "chain": { "family": "tron", "network": "tron:3448148188", "chainId": "3448148188" }
}
```

Failure:

```json
{
  "schema": "wallet-cli.result.v1",
  "success": false,
  "command": "tx.info",
  "error": { "code": "rpc_error", "message": "human-readable only" },
  "meta": { "durationMs": 42, "warnings": [] },
  "chain": { "family": "tron", "network": "tron:3448148188", "chainId": "3448148188" }
}
```

- Require `schema == "wallet-cli.result.v1"`; stop on a different schema.
- `command` is the canonical operation id, not necessarily the literal words entered.
- `data` exists on success; `error` exists on failure.
- `chain` is present only for chain operations.
- `error.code` is machine-readable. `error.message` is unstable and must not be parsed.
- `bigint` values and on-chain amounts are decimal strings. Keep those fields as strings or
  arbitrary-precision integers; never use floating point for them.
- Other counters and configuration values follow the command-specific documentation and schema and
  may be JSON numbers. For example, `chain params.data.value` is a number in wallet-cli 4.16.0; do
  not coerce a field based only on it coming from the chain.
- Ordered listings echo their ordering in `meta.query` as `{orderBy, sort}`; listings without an
  ordering flag omit it.
- `sunswap` and `sunpump` token amounts are base-unit strings carried with their `decimals`
  (`{address, symbol, decimals, amount}`, `lpAmount` / `lpDecimals`, `tokensIn` / `tokenDecimals`).
  Scale with the sibling `decimals`, never an assumed one. A V3 or V4 position's `liquidity`,
  `liquidityAfter`, and `liquidityExpected` have no decimals; do not scale them.
- JSON identifies tokens by address only. Text output may show symbols that JSON omits.
- In `account history`, `status: "unknown"` is not success. A TRC10 row carries `assetId` and
  `rawAmount`; an empty `amount` means the human amount is unavailable, not zero.

## Warnings

`meta.warnings` is always an array whose elements may be either strings or objects:

```json
["plain notice", {"code":"owner_lockout_partial","message":"human-readable notice"}]
```

Normalize both forms for display. Branch only on object `code`, never warning message text. A
warning does not change `success`; high-risk warning codes can require stopping even on exit `0`.

For `permission update`, stop on `owner_lockout` and require explicit review of
`owner_lockout_partial` or `active_can_update_permission` before proceeding.

## Error decisions

- Exit `2`, including `usage_error`, `missing_option`, `invalid_option`, and `invalid_value`: inspect
  the leaf `--json-schema`, fix the request, then retry.
- `error.details.outcome: "unknown"` (on `timeout`, `rpc_error`, `invalid_node_response`, or a
  payment or service write): the request may have acted, whatever the code's retry class says.
  Never rebuild or re-sign it. Reconcile first:
  - a chain broadcast: look up `error.details.txId` with `tx status`, or rebroadcast the same
    signed transaction with `tx broadcast` (`alreadyKnown: true` when the node holds it);
  - `tx multisig`: list the account's TronLink collection with `tx multisig` on the same network,
    even when a `txId` is present;
  - GasFree: follow a known `traceId` with `gasfree trace`, or compare the `nonce` from
    `gasfree info` with `error.details.nonce`;
  - `sunpump launch` (`launch_outcome_unknown`): `sunpump token-search <symbol>`.
- `timeout` without `outcome`: no transaction was sent except the approvals in
  `error.details.approvalTxIds`, and a pending one may still confirm; check them first.
  Increase the timeout only if still within the task deadline.
- `rpc_error`: verify network, endpoint, address, funds, resources, and permission. Do not retry
  blindly.
- `auth_required` or `auth_failed`: use the approved secret channel or return control to the user;
  never request the password in chat.
- `insufficient_balance`, `insufficient_token_balance`, or `insufficient_stake`: stop and report
  the shortfall.
- `internal_error`: stop and report; do not loop.
- If `error.details.matches` exists, present the structured candidates and ask the user to select
  rather than parsing `error.message`.

Codes that need a specific action:

| Code | Exit | Action |
|---|---|---|
| `chain_id_mismatch` | 1 | The transaction or typed data names another chain than `--network`. Stop and report; never switch the network on your own |
| `signed_payload_mismatch` | 1 | A signature, including any Ledger signature, does not match the account or payload; it was not used. Stop and report; do not retry |
| `unsupported_network_capability` | 2 | The selected network does not offer the command. Choose a supported network from the command routing reference; never switch a write to mainnet without asking |
| `launch_outcome_unknown` | 1 | Never retry. Run `sunpump token-search <symbol>` to find out whether the token exists |
| `no_matching_route` | 1 | The same request may succeed later; a retry still needs fresh authorization |
| `permit_mismatch` / `router_call_mismatch` | 1 | A CLI safety check refused to sign or send. Stop and report; do not retry |
| `pool_not_found` / `pool_already_exists` / `position_not_found` | 1 | Report; the user adjusts the pair, pool key, or position id |
| `launchpad_trading_closed` | 1 | The curve is awaiting launch or has launched (`sunpump token-info`). If launched, move to `sunswap swap` with a new preview |
| `launchpad_token_not_found` | 1 | Report; the address or network is wrong |
| `ledger_setting_required` / `device_not_found` / `device_unavailable` / `device_disconnected` | 1 | Return device setup to the user; do not retry on your own |
| `tx_expired` | 1 | The transaction expired before, during, or after signing, or the node rejected it as expired. Rebuild, re-sign, and confirm again |
| `provider_rate_limited` | 1 | Also raised by SunSwap and SunPump. Back off for `error.details.retryAfterSeconds` when present |

## Pagination

Commands that accept `--limit` and `--offset` report:

```json
{"offset":0,"limit":50,"total":null}
```

under `meta.pagination`. `total: null` means the endpoint exposes no total. Page until a short page
is returned; do not treat null as zero and do not fetch unbounded pages without need.

The `sunswap` listings (`pool-list`, `pool-search`, `position-list`, `token-list`, `token-search`)
and `sunpump` listings (`token-list`, `token-search`) are paginated too:

- SunSwap serves only the first 1000 rows of any ordering. `--offset` must be a multiple of
  `--limit`, and a window past row 1000 fails locally with `invalid_value` (exit 2) before any
  request. `meta.pagination` may add `hasMore`. `sunswap pool-list --min-tvl` can come back short
  with `hasMore: true` and a `sunswap_scan_truncated` warning.
- SunPump always reports `total: null`; a page shorter than `--limit` is the end.

## Transaction state

Broadcasting commands wait for confirmation by default and report the outcome in `data.stage`:
`confirmed`, `failed`, or `submitted`. A mined revert returns exit `0`, `success: true`, and
`stage: "failed"`. `submitted` is pending, not completed: the wait ended first (the time limit ran
out, or polling hit an error that cannot be retried unchanged; a warning says which), or
`--no-wait` was passed:

```json
{"kind":"send","stage":"submitted","txId":"..."}
```

After a `submitted` stage, poll `tx status` using a finite deadline:

| `data.state` | Terminal | Action |
|---|---|---|
| `confirmed` | yes | Report completion with txid/block |
| `failed` | yes | Report the on-chain failure; do not retry automatically |
| `pending` | no | Continue within the deadline |
| `not_found` | no | Continue within the deadline; verify network before concluding |

GasFree is different: `gasfree transfer` returns `traceId` and follows the provider states until
`SUCCEED` or `FAILED` by default. After a `submitted` stage, poll `gasfree trace`; do not pass a
trace id to `tx status`.

### Commands that send several transactions

The `sunswap` liquidity commands, a `sunswap swap` that spends a token (router or bonding curve),
and a first `sunpump sell` send approvals before the main transaction. Their ids are in
`data.approvalTxIds`, in the order sent, beside the main `txId`. Approvals always wait for
confirmation, also with `--no-wait`, which applies only to the main transaction. Approvals and the
main transaction share the `--timeout` deadline; an approval that does not confirm in time stops
the command with `timeout`. If a later step fails, the original error code is kept and
`error.details.approvalTxIds` lists the approvals already submitted. They are not rolled back;
check each before any retry.

With `--build-only`, such a command returns `data.transactions[]` instead of a single transaction
whenever an approval is still needed: each entry has `purpose` `"approval"` or `"main"`, in the
order they must be sent. Sign and broadcast each one only after the one before it confirms; the
main call reverts if it lands before its approval. These transactions expire one hour after they
are built, and the main call of `add-liquidity` / `remove-liquidity` is also bounded by
`--deadline` (default 30 minutes from the build). `feeCovers` is `"approvals"`, because the main
call cannot be priced before its approvals exist. With no approval needed, the output is the
ordinary single unsigned transaction.

### `sunpump launch`

A launch is created by the SunPump service, not by a local transaction: there is no `stage`,
`confirmed`, fee, `--wait`, or `--no-wait`, and `data.token.owner` is the creator the service
chose, not the local account. Use `tx info` on `createTxHash` to see whether it is on chain; an
`rpc_error` there is inconclusive (not on chain yet, or the node request failed), not a failed
launch.

### Measured and quoted amounts

A confirmed trade reports amounts read from its own receipt with `amountsEstimated: false`. If the
receipt cannot be read, the pre-trade estimate stays, `amountsEstimated` is `true`, a warning says
why, and the trade remains successful. A router swap's `priceImpactPercent` and trading fee are
always quoted figures (`priceImpactEstimated: true`).

## Duplicate prevention

- One authorized request produces at most one transaction unless the user explicitly authorizes a
  batch or the command itself sends approvals first (see commands that send several transactions).
- Persist or retain the `txId`/`traceId` immediately after submission.
- After timeout, lost output, `pending`, or `not_found`, reconcile within a bounded period before
  considering another broadcast.
- Stop on first batch failure by default and report the per-item states.

## Secret channels

Secrets are never valid in argv or environment variables.

- Use CLI-supported flags such as `--password-stdin`, `--tx-stdin`, `--message-stdin`, or
  `--api-key-stdin` (service credentials for `config`) only with an approved, non-logging stdin
  source.
- Only one `*-stdin` option may consume stdin in a single process.
- Mnemonic/private-key import and `change-password` require a hidden interactive TTY; return those
  steps to the user.
- Never capture secret-producing output such as `address generate --print-secret` in model context.

## Fee estimates

A dry run's `fee` is what the chain's simulation predicts and is a lower bound; never derive
`--fee-limit` from it. `feeCovers` states what the figure covers:

| `feeCovers` | `fee` covers |
|---|---|
| `"all"` | the whole operation |
| `"approvals"` | the approval transactions only; the main call cannot be simulated yet |
| `"none"` | nothing; `fee` is a `{feeModel, note}` object and `feeUnavailableReason` says why |

When reporting a fee, say what it covers.

## x402 responses

- A binary response (images, PDF, archives, `application/octet-stream`) requires `--out`; without
  it, `x402 pay` fails with `invalid_option` (exit 2). Choose `--out` before requesting a binary
  resource.
- When `error.details` carries `settled: true` and `retryPayment: false`, the payment went through.
  Do not pay again; reconcile with the provider using the transaction hash.

## Version boundary

This contract is pinned to wallet-cli `4.16.0`. If the installed version differs, stop and obtain
approval before changing it. Do not silently apply this reference to another version.
