# Safety and Authorization

Read this reference before any local wallet mutation, signature, broadcast, or on-chain write.

## Networks

| Network | Meaning | Policy |
|---|---|---|
| `tron:mainnet` | Production; real funds and persistent public state | Preview and explicit confirmation before funds-moving or externally visible writes |
| `tron:nile` | Primary testnet | Clearly authorized ordinary writes may proceed without a second confirmation |
| `tron:shasta` | Alternate testnet | Clearly authorized ordinary writes may proceed without a second confirmation |

Always pass the canonical network explicitly for chain operations. Never infer mainnet from an
address because TRON addresses are identical across networks.

## Confirmation matrix

| Operation | Testnet | Mainnet |
|---|---|---|
| Read-only query | Execute within scope | Execute within scope |
| Ordinary wallet or chain write | User's clear request authorizes the exact operation | Preview, then obtain explicit confirmation immediately before execution |
| Funds transfer, broadcast, contract write, staking, voting, governance, exchange, or GasFree transfer | User's clear request authorizes the exact operation | Preview, then obtain explicit confirmation immediately before execution |
| High-risk local or permission operation | Always preview where possible and confirm | Always preview where possible and confirm |

A confirmation is scoped to the displayed network, account, target, command, amount, asset,
parameters, and one execution. Any change requires a new confirmation.

## High-risk operations on every network

### `permission update`

This replaces the entire permission structure. A wrong owner group can lock the account permanently.

1. Read the current structure with `permission show`.
2. Generate or review the complete replacement file.
3. Run `permission update --dry-run -o json`.
4. Inspect the resulting owner/witness/active groups, thresholds, key weights, and operation bitmap.
5. Stop on `owner_lockout`; explicitly surface `owner_lockout_partial` and
   `active_can_update_permission` warnings.
6. Obtain explicit confirmation of the rendered replacement.
7. Execute once, preferably with `--wait`, and inspect `data.stage` plus warnings.

Never reconstruct a permission bitmap from memory when the CLI can export or decode it.

### `delete`

Confirm the exact account id/label and cascade impact. Deleting an HD seed root can remove its
derived accounts. Do not infer that a usable backup exists unless the user verifies it.

### `backup`

Confirm the exact account, export format, and destination path. The output is secret material.
Never read the created file, overwrite an existing path, or include its contents in model context.

### `address generate --print-secret`

The option writes a private key to stdout. Do not run it in an agent session. Prefer the default
file output and tell the user where it was written without reading the file.

### Signing arbitrary content

For `message sign`, `typed-data sign`, transaction signing, and contract writes, show the exact
human-meaningful payload, domain, network, account, permission id, and destination before signing.
Treat opaque or untrusted payloads as high risk. Never sign a challenge whose purpose is unclear.

### One-shot account operations

`account activate` charges the active payer. On-chain account name and id settings are effectively
one-time. Confirm payer, target, name/id, network, and irreversibility before execution.

## Preview contents

Before a mainnet confirmation, show all fields available for the operation:

- canonical network;
- source account label/id and public address;
- recipient, contract, proposal, witness, exchange, permission, or other target;
- human amount plus raw base-unit amount when available;
- token symbol and verified contract/asset id;
- fee limit, resource, duration, lock, slippage/min-return, permission id, and other material flags;
- whether the command will build, sign, submit, wait, write a file, or expose a secret;
- dry-run estimates and warnings.

Do not ask for confirmation using only an opaque command string when the values can be explained.

## Secret and file safety

- Never request or display passwords, mnemonics, private keys, signing material, or service
  credentials.
- Never read wallet stores, keystores, generated private-key files, backup outputs, or credential
  fields into model context.
- Do not pass secrets through argv, environment variables, shell history, logs, or temporary files.
- Do not overwrite output files. Respect `output_exists` and ask the user for a new destination.
- Public addresses, txids, block numbers, balances, token metadata, and transaction receipts are
  safe to report unless the user imposes a stricter privacy boundary.

## Retry and stopping rules

- Never retry a successful submission.
- A timeout during signing or broadcasting is ambiguous. Check `tx status`, transaction history,
  or the relevant provider trace before any retry.
- `pending` and `not_found` are not permission to resend.
- Do not continue a batch after failure unless the user explicitly requested best-effort behavior.
- Stop when the requested operation reaches a terminal state, the task deadline expires, or user
  input is required. Report unresolved txids/trace ids for later reconciliation.
