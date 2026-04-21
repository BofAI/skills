# Agent Wallet Skill

Wallet management and signing skill for EVM and TRON.

## Quick Start

Use this skill when the user needs to create a wallet, inspect addresses, switch the active wallet, or sign transactions and messages through the `agent-wallet` CLI.

## What It Covers

- First-time wallet setup
- Listing wallets and checking the active wallet
- Resolving EVM and TRON addresses
- Switching the active wallet
- Signing transactions, messages, and typed data

## Files

- [SKILL.md](SKILL.md) - Full operational rules and safety constraints
- [commands-reference.md](commands-reference.md) - CLI command reference
- [shell-quoting.md](shell-quoting.md) - Quoting guidance for shell-safe command execution
- [scripts/generate-password.js](scripts/generate-password.js) - Helper for quick wallet setup

## Important Constraints

- Never handle raw private keys or mnemonics directly in conversation.
- Always run `agent-wallet <command> --help` before executing the command.
- `remove`, `reset`, and `change-password` are user-only operations and must not be executed by the agent.

## Installation

```bash
npm install -g @bankofai/agent-wallet
```

## License

MIT
