# Command Routing

Use this reference to select a wallet-cli command family. It summarizes version 4.12.0; the CLI's
generated schema remains authoritative for exact flags and combinations.

## Discover the live command contract

```bash
wallet-cli --json-schema
wallet-cli <group> --json-schema
wallet-cli <group> <command> --json-schema
```

Root and group schemas return command catalogs. A leaf schema describes its accepted inputs. Use
`--help` only when the schema does not communicate enough human meaning.

Every operational example below must also include `-o json`. Chain operations must include an
explicit `--network tron:mainnet|tron:nile|tron:shasta`.

## Local wallet and account lifecycle

| Goal | Command family | Notes |
|---|---|---|
| Create an HD wallet | `create` | Hidden password prompt or supported stdin channel |
| Import an account | `import mnemonic|private-key|keystore|ledger|watch` | Human-only; the Agent must not invoke any import subcommand |
| List/select accounts | `list`, `use`, `current` | `--account` can select without changing the active account |
| Derive or rename | `derive`, `rename` | Local wallet-state changes |
| Back up | `backup` | Human-only; writes secret recovery material |
| Delete | `delete` | Human-only; HD-root deletion can cascade |
| Change password | `change-password` | Human-only; hidden interactive TTY operation |
| Generate an unstored keypair | `address generate` | `--print-secret` exposes a private key to stdout |

## Read-only chain operations

| Goal | Command family |
|---|---|
| Account balance, details, history, portfolio | `account balance|info|history|portfolio` |
| Transaction state or receipt | `tx status|info` |
| Account permissions | `permission show` |
| Staking and delegation state | `stake info|delegated` |
| Votes and rewards | `vote list|status`, `reward balance` |
| Blocks and node state | `block`, `chain params|prices|node` |
| Token metadata and balances | `token info|balance|list` |
| Contract reads and metadata | `contract call|info` |
| Governance proposals | `proposal list|show` |
| TRC10 assets | `asset info|list` |
| Protocol exchange pairs | `exchange show|list` |
| GasFree state | `gasfree info|trace` |

## Transfers and transaction lifecycle

Use `tx send` for TRX, TRC20, or TRC10 transfers. It accepts exactly one amount representation and
at most one token selector:

```bash
wallet-cli tx send --to T... --amount 1 --network tron:nile --dry-run -o json
```

- No selector means TRX.
- `--token` resolves an address-book symbol.
- `--contract` selects a TRC20 contract address.
- `--asset-id` selects a TRC10 id.
- `--amount` is a human-unit decimal string; `--raw-amount` is an unscaled integer string.
- `--dry-run` builds and estimates without signing or broadcasting.
- `--sign-only` emits signed transaction hex; `--build-only` emits unsigned hex.
- `--wait` polls after broadcast but can still return `data.stage: "submitted"` when its wait cap
  expires.

Use `tx sign` and `tx approvals` for file-based multi-signature artifacts. Use `tx multisig` for the
TronLink collaboration service. Broadcast only after signature threshold validation:

```text
build unsigned → collect signatures → inspect approvals → dry-run broadcast → broadcast once
```

`tx broadcast` validates expiration and signature weight before submission. Its default success
still means submitted, not confirmed.

## Resource, governance, and contract writes

| Goal | Command family |
|---|---|
| Stake and delegate resources | `stake freeze|unfreeze|withdraw|cancel-unfreeze|delegate|undelegate` |
| Vote or claim rewards | `vote cast`, `reward withdraw` |
| Activate or name an account | `account activate`, `account set` |
| Contract write/deploy/governance | `contract send|deploy|clear-abi|set-origin-energy-limit|set-user-resource-percent|create2` |
| Replace permissions | `permission update` |
| GasFree transfer | `gasfree transfer` |
| Proposal governance | `proposal create|approve|delete` |
| Super-representative operation | `witness create|update|set-brokerage` |
| TRC10 lifecycle | `asset issue|update|participate|unfreeze` |
| Protocol exchange | `exchange create|inject|withdraw|trade` |

Treat every command in this section as a write. Apply the network and confirmation matrix in
[safety.md](safety.md) before execution.

## Local address books and configuration

- `contact add|list|remove` manages recipient aliases accepted by `--to`.
- `token add|list|remove|info|balance` manages token metadata and queries token state.
- `config` changes CLI configuration, including service credentials. Never print or read credential
  values into model context.
- `networks` lists canonical network ids.
- `encoding convert` converts or validates address and binary encodings locally.
- `message sign` and `typed-data sign` create externally usable signatures; treat them as visible
  writes and confirm the exact payload/domain before signing.

## Scope boundary

This CLI manages wallets and generic TRON operations. Route SunSwap swaps, pool discovery, pricing,
and liquidity management to the SunSwap skill. Route non-TRON chains to their own wallet tools.
