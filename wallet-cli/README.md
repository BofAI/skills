# TRON Wallet CLI Skill

Agent instructions for operating the TypeScript `wallet-cli` safely through its machine-readable
interface. The Skill covers TRON accounts, transfers, staking, governance, contracts, signing, and
chain queries and is pinned to `@tron-walletcli/wallet-cli@4.12.0`.

## Installation

The recommended installation path is the repository's standard interactive installer:

```bash
npx skills add https://github.com/BofAI/skills.git
```

Select `wallet-cli` and the target agent platform when prompted. This installs the Skill but does
not silently modify global npm packages.

For an optional wallet-cli-specific installation flow:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/main/wallet-cli/install.sh | sh
```

The script installs the Skill and asks for explicit confirmation before running:

```bash
npm install --global --no-fund --no-audit @tron-walletcli/wallet-cli@4.12.0
```

Declining the prompt or passing `--skip-cli-install` installs only the Skill. Use `--dry-run` to
preview the operation:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/main/wallet-cli/install.sh | sh -s -- --dry-run
```

## Contents

- [SKILL.md](SKILL.md) — operational rules and version boundary
- [install.sh](install.sh) — optional confirmed installation flow
- [references/commands.md](references/commands.md) — command-family routing
- [references/machine-interface.md](references/machine-interface.md) — JSON, exit-code, and transaction-state contract
- [references/safety.md](references/safety.md) — authorization, confirmation, secret, and retry rules

## Requirements

- Node.js 20 or newer when installing the npm CLI
- Git for the optional installer
- Explicit network selection for chain operations

The Skill never authorizes an installer or Agent to collect wallet passwords, mnemonics, or private
keys.
