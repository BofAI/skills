# Agent Wallet — Commands Reference

> **Before using any command, run `agent-wallet <command> --help` to verify flags for the installed version.**
> This reference reflects current source; CLI flags may differ across versions.

## Wallet Types

| Type | Agent can create? | Notes |
|------|------------------|-------|
| `local_secure` | ✅ via `--generate` | Encrypted Keystore V3, requires password. Recommended for production. |
| `raw_secret` | ❌ disabled | Plaintext key from env var — agent cannot safely configure; tell user to set it up manually. |
| `privy` | ✅ via `--app-id/--app-secret/--privy-wallet-id` | Uses Privy API credentials (not private keys) — safe for agent to pass. |

## Global Flags (all commands)

| Flag | Short | Description |
|------|-------|-------------|
| `--dir <path>` | `-d` | Secrets directory (default: `~/.agent-wallet`) |
| `--help` | `-h` | Show command help |

## `start [local_secure\|raw_secret\|privy]`

Initialize + create default wallet in one step.

| Flag | Short | Notes |
|------|-------|-------|
| `--wallet-id <id>` | `-w` | Wallet ID |
| `--generate` | `-g` | Generate new key pair (`local_secure` only, no `raw_secret`) ← **agent use this** |
| `--private-key <hex>` | `-k` | Import from private key — **user runs manually in terminal, never via agent** |
| `--mnemonic <phrase>` | `-m` | Import from mnemonic — **user runs manually in terminal, never via agent** |
| `--derive-as <profile>` | | `eip155` or `tron` derivation profile (used with `--mnemonic`) |
| `--mnemonic-index <n>` | `-mi` | Derivation account index (default: `0`) |
| `--app-id <id>` | | Privy app ID (`privy` only) |
| `--app-secret <secret>` | | Privy app secret (`privy` only) |
| `--privy-wallet-id <id>` | | Privy wallet ID (`privy` only) |
| `--override` | | Skip confirmation when wallets already exist |
| `--password <pw>` | `-p` | Master password |
| `--save-runtime-secrets` | | Persist password to runtime secrets file |

## `init`

Initialize secrets directory and set master password.

| Flag | Short | Notes |
|------|-------|-------|
| `--password <pw>` | `-p` | Master password |
| `--save-runtime-secrets` | | Persist password |

## `add [local_secure\|raw_secret\|privy]`

Add a new wallet. Same flags as `start`, minus `--override`.

## `list`

No extra flags.

## `use <wallet-id>`

Positional argument only. No extra flags. **In agent context, always pass `<wallet-id>` explicitly — interactive selection unavailable.**

## `inspect <wallet-id>`

| Flag | Notes |
|------|-------|
| `--show-address` | Derive and display EVM + TRON addresses (requires password for `local_secure`) |

## `resolve-address [wallet-id]`

| Flag | Short | Notes |
|------|-------|-------|
| `--password <pw>` | `-p` | Master password |

Omitting `wallet-id` shows interactive selection — **always pass it explicitly in agent context.**

## `remove <wallet-id>`

| Flag | Short | Notes |
|------|-------|-------|
| `--yes` | `-y` | Skip confirmation prompt (**required in agent context**) |

## `sign tx <payload>`

| Flag | Short | Notes |
|------|-------|-------|
| `--network <net>` | `-n` | Target network, e.g. `eip155:1`, `tron:mainnet` (**required**) |
| `--wallet-id <id>` | `-w` | Wallet to sign with (defaults to active wallet) |
| `--password <pw>` | `-p` | Master password |
| `--save-runtime-secrets` | | Persist password |

## `sign msg <message>`

Same flags as `sign tx`.

## `sign typed-data <data>`

Same flags as `sign tx`. EVM only.

## `change-password`

| Flag | Short | Notes |
|------|-------|-------|
| `--password <pw>` | `-p` | Current master password |
| `--new-password <pw>` | | New master password (skip interactive prompt) |
| `--save-runtime-secrets` | | Persist new password |

## `reset`

| Flag | Short | Notes |
|------|-------|-------|
| `--yes` | `-y` | Skip confirmation (**required in agent context**) |
