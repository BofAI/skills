---
name: agent-wallet
description: 'Use when the user asks to create a wallet, check wallet addresses, sign transactions or messages, switch active wallets, or perform any blockchain signing operation using the agent-wallet CLI. Supports EVM and TRON networks.'
compatibility: Requires Node.js 20+.
metadata:
  author: BofAI
  homepage: 'https://github.com/BofAI/agent-wallet'
  requires:
    bins: ['node', 'agent-wallet']
    env:
      - name: AGENT_WALLET_PASSWORD
        description: 'Master password for encrypted wallets.'
        required: false
      - name: AGENT_WALLET_DIR
        description: 'Wallet config directory (default: ~/.agent-wallet)'
        required: false
---

# Agent Wallet Skill

**CRITICAL: Never handle private keys or mnemonics directly.** All cryptographic operations go through the CLI. Never read keystore files, parse private keys, or expose mnemonics in conversation — use CLI commands for everything.

This skill is **sign-only** — transaction building and broadcasting are out of scope.

## Installation

If `agent-wallet` is not installed, ask the user: **stable or beta version?**

```bash
# Node.js — stable
npm install -g @bankofai/agent-wallet

# Node.js — beta
npm install -g @bankofai/agent-wallet@beta
```

## Interaction Workflow

Follow this 4-step pattern for every user request:

**Step 1 — Check current state, then understand intent**

Always run `agent-wallet list` first to see existing wallets and active wallet. Never assume it's a first-time setup.

- **No wallets exist** → **first present the wallet type options with descriptions** (do not skip this), then ask the user to choose. Present as:
  - `local_secure` — private key encrypted locally with a master password. Recommended for production.
  - `privy` — uses Privy hosted wallet via API credentials (App ID + App Secret + Privy Wallet ID). No private key stored locally.
  - (`raw_secret` is disabled — user must configure manually, agent cannot set it up)
- **Wallets already exist** → use `add` instead of `start`; do NOT re-run `start` (it will error unless `--override` is passed)

**Step 2 — Look up the command (MANDATORY, no exceptions)**

Run `agent-wallet <command> --help` BEFORE executing. Do not skip this step even if you think you know the flags.

```bash
agent-wallet start --help        # always run first
agent-wallet start local_secure --help   # then subcommand help if applicable
```

**Step 3 — Ask once, ask everything**

In a single message, collect all required information. Always include these privacy-sensitive choices with explanation:

- **`--save-runtime-secrets`**: saves password unencrypted to `~/.agent-wallet/runtime_secrets.json`. Convenient on personal machines; avoid on shared environments.
- **`--dir`**: custom secrets directory. Ask only if user may have a non-default setup.

**Step 4 — Execute**

Use the user's answers to construct one complete command with all flags. Never run partial commands expecting to be prompted.

## Restricted Operations

`remove`, `reset`, and `change-password` are **agent-restricted** — the agent must NOT execute these commands. Misuse can cause permanent, unrecoverable loss of wallet access (private keys cannot be restored).

**When the user requests one of these:**
1. Explain what the operation does and that it is irreversible
2. Tell the user to run the command themselves in their terminal
3. Provide the exact command to copy-paste, but do not execute it

```bash
# Examples to show the user — do NOT run via agent
agent-wallet remove <id> --yes
agent-wallet reset --yes
agent-wallet change-password -p 'OldPass' --new-password 'NewPass'
```

## Red Flags — Use CLI Instead

| Thought | Correct action |
|---------|---------------|
| "Let me read `wallets_config.json`" | `agent-wallet list` |
| "I can derive the address from the key" | `agent-wallet resolve-address <id>` |
| "User should run the command themselves since I need a password" | Ask user for password in conversation, then use `--password '<pw>'` in the Bash command — agent Bash execution does not write to shell history |
| "Let me build the transaction first" | Out of scope — request payload from user |
| "User wants to import a key/mnemonic" | Tell user to run `add --private-key` / `add --mnemonic` **themselves** in terminal — never pass key material through this conversation |
| "I already know the flags, I'll skip `--help`" | **Always run `--help` first.** Non-interactive errors happen when subcommands or required flags are missing. `--help` takes 1 second and prevents failed runs. |

## Password Resolution (first match wins)

1. Runtime secrets (`~/.agent-wallet/runtime_secrets.json`) ← preferred after first setup
2. `AGENT_WALLET_PASSWORD` env var
3. `--password '<pw>'` flag ← **use this in agent context when runtime secrets not yet set up**
4. Interactive prompt (unavailable in non-interactive contexts)

> `--password` exposes password in the user's shell history only when the user types it manually in a terminal. When the agent runs commands via Bash tool, there is no interactive shell history. It is safe and correct for the agent to ask the user for a password in conversation and pass it via `--password`.

## Agent Context Rules

In agent contexts `stdin` is not a TTY — **all interactive prompts are disabled. Always pass every required flag explicitly or the command will hang/fail.**

| Situation | Required flags |
|-----------|--------------|
| `start`, `add` (`local_secure`) | `--wallet-id <id>` + `--generate` |
| `start`, `add` (`privy`) | `--wallet-id <id>` + `--app-id` + `--app-secret` + `--privy-wallet-id` |
| `use`, `inspect`, `resolve-address` | Positional `<wallet-id>` |
| `sign *` | `--network <net>` |
| No runtime secrets configured | `--password <pw>` |

**Always quote user-supplied strings** to prevent shell expansion of `!`, `$`, `&`, `*`, etc. Single quotes `'...'` work for bash, zsh, PowerShell 7, and fish. PowerShell 5 and cmd.exe need different handling for JSON payloads — see `shell-quoting.md`.

```bash
agent-wallet sign tx '{"to":"0x...","chainId":1}' --network eip155:1
```

## Commands

Run `agent-wallet <command> --help` for full options. See `commands-reference.md` for all flags.

| Command | Purpose |
|---------|---------|
| `start local_secure --wallet-id <id> --generate` | First-time setup: init + create encrypted wallet |
| `list` | List all wallets and active marker |
| `resolve-address [id]` | Show EVM + TRON addresses for a wallet |
| `inspect <id> [--show-address]` | Show wallet metadata (+ addresses) |
| `use <id>` | Switch active wallet |
| `add local_secure --wallet-id <id> --generate` | Add a new encrypted wallet |
| `sign tx '<json>' --network <net>` | Sign a transaction |
| `sign msg '<text>' --network <net>` | Sign a message (EIP-191) |
| `sign typed-data '<json>' --network <net>` | Sign EIP-712 typed data (EVM only) |
| `remove <id> --yes` | ❌ **agent-restricted** — tell user to run manually |
| `change-password` | ❌ **agent-restricted** — tell user to run manually |
| `reset --yes` | ❌ **agent-restricted** — tell user to run manually |

## Network Identifiers

Format: `eip155:<chainId>` for EVM, `tron:mainnet` or `tron:nile` for TRON.

Common: `eip155:1` (Ethereum), `eip155:137` (Polygon), `eip155:56` (BSC), `eip155:42161` (Arbitrum), `eip155:8453` (Base).

One wallet derives separate EVM and TRON addresses from the same key — use `resolve-address` to see both.

## Error Handling

| Error | Resolution |
|-------|------------|
| `No wallets configured` | `agent-wallet start --save-runtime-secrets` |
| `Password required` | Re-run setup with `--save-runtime-secrets` |
| `DecryptionError` / wrong password | Check `AGENT_WALLET_PASSWORD` or runtime secrets |
| `Already initialized` | Directory already set up — skip `init`, proceed to `add` |
| `Wallet not found: <id>` | `agent-wallet list` to see valid IDs |
| `Network not supported` | Use `eip155:<chainId>` or `tron:mainnet`/`tron:nile` |
| `Private key must be 32 bytes` | Invalid key format — user-side issue, run import manually |
