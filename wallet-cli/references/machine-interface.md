# Machine Interface Contract

Use this reference when parsing results, handling errors, polling transactions, paginating, or
providing secrets non-interactively. It summarizes the stable `wallet-cli.result.v1` contract in
wallet-cli 4.12.0.

## Calling convention

```bash
wallet-cli <command> -o json [--network <id>] [--timeout <ms>] [--account <id|label>]
```

JSON mode writes exactly one terminal result object to stdout. Diagnostics go to stderr.

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
  "chain": { "family": "tron", "network": "tron:nile", "chainId": "nile" }
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
  "chain": { "family": "tron", "network": "tron:nile", "chainId": "nile" }
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
  may be JSON numbers. For example, `chain params.data.value` is a number in wallet-cli 4.12.0; do
  not coerce a field based only on it coming from the chain.

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
- `timeout`: increase the timeout only if still within the task deadline. If broadcasting may have
  occurred, reconcile transaction state before retrying.
- `rpc_error`: verify network, endpoint, address, funds, resources, and permission. Do not retry
  blindly.
- `auth_required` or `auth_failed`: use the approved secret channel or return control to the user;
  never request the password in chat.
- `insufficient_balance` or `insufficient_token_balance`: stop and report the shortfall.
- `internal_error`: stop and report; do not loop.
- If `error.details.matches` exists, present the structured candidates and ask the user to select
  rather than parsing `error.message`.

## Pagination

Commands that accept `--limit` and `--offset` report:

```json
{"offset":0,"limit":50,"total":null}
```

under `meta.pagination`. `total: null` means the endpoint exposes no total. Page until a short page
is returned; do not treat null as zero and do not fetch unbounded pages without need.

## Transaction state

Broadcasting commands normally return:

```json
{"kind":"send","stage":"submitted","txId":"..."}
```

`submitted` is pending, not completed.

- With `--wait`, inspect `data.stage`: `confirmed`, `failed`, or still `submitted` after the wait
  cap. A mined revert can return exit `0`, `success: true`, and `stage: "failed"`.
- Without `--wait`, poll `tx status` using a finite deadline:

| `data.state` | Terminal | Action |
|---|---|---|
| `confirmed` | yes | Report completion with txid/block |
| `failed` | yes | Report the on-chain failure; do not retry automatically |
| `pending` | no | Continue within the deadline |
| `not_found` | no | Continue within the deadline; verify network before concluding |

GasFree is different: `gasfree transfer` returns `traceId`. Poll `gasfree trace` through provider
states until `SUCCEED` or `FAILED`; do not pass a trace id to `tx status`.

## Duplicate prevention

- One authorized request produces at most one transaction unless the user explicitly authorizes a
  batch.
- Persist or retain the `txId`/`traceId` immediately after submission.
- After timeout, lost output, `pending`, or `not_found`, reconcile within a bounded period before
  considering another broadcast.
- Stop on first batch failure by default and report the per-item states.

## Secret channels

Secrets are never valid in argv or environment variables.

- Use CLI-supported flags such as `--password-stdin`, `--tx-stdin`, or `--message-stdin` only with
  an approved, non-logging stdin source.
- Only one `*-stdin` option may consume stdin in a single process.
- Mnemonic/private-key import and `change-password` require a hidden interactive TTY; return those
  steps to the user.
- Never capture secret-producing output such as `address generate --print-secret` in model context.

## Version boundary

This contract is pinned to wallet-cli `4.12.0`. If the installed version differs, stop and obtain
approval before changing it. Do not silently apply this reference to another version.
