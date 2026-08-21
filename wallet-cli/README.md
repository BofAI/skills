# TRON Wallet CLI Skill

Agent instructions for operating the TypeScript `wallet-cli` safely through its machine-readable
interface. The Skill covers TRON accounts, transfers, staking, governance, contracts, signing, and
chain queries and is pinned to `@tron-walletcli/wallet-cli@4.12.0`.

## Installation

Choose either method below. Both install Skill version `1.0.0` and use
`@tron-walletcli/wallet-cli@4.12.0`.

### Method 1: Install the CLI, then the Skill

Install the pinned npm CLI first, then install the Skill through the standard Skills CLI:

```bash
npm install --global --no-fund --no-audit @tron-walletcli/wallet-cli@4.12.0
npx skills add BofAI/skills --skill wallet-cli --global --yes
```

The `npx skills` command installs only the Skill; it does not install or update the `wallet-cli`
npm package.

### Method 2: Install both with one script

On macOS, Linux, Git Bash, or WSL, run the repository installer:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/main/wallet-cli/install.sh | sh
```

The script installs or verifies the pinned CLI and installs the Skill without prompting by default.
It requires a POSIX shell and standard utilities such as `mktemp`, `cp`, `mv`, and `mkdir`.

Use `--ask` to show the complete plan and require one confirmation, `--skill-only` to leave npm
packages unchanged, or `--dry-run` to preview the operation:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/main/wallet-cli/install.sh | sh -s -- --ask
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/main/wallet-cli/install.sh | sh -s -- --skill-only
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/main/wallet-cli/install.sh | sh -s -- --dry-run
```

After either method, verify the CLI version:

```bash
wallet-cli --version
```

## Contents

- [SKILL.md](SKILL.md) — operational rules and version boundary
- [install.sh](install.sh) — one-command Skill and pinned CLI setup
- [references/commands.md](references/commands.md) — command-family routing
- [references/machine-interface.md](references/machine-interface.md) — JSON, exit-code, and transaction-state contract
- [references/safety.md](references/safety.md) — authorization, confirmation, secret, and retry rules

## Requirements

- Node.js 20 or newer when installing the npm CLI
- Git, a POSIX shell, and standard POSIX utilities for the one-command installer
- Explicit network selection for chain operations

The Skill never authorizes an installer or Agent to collect wallet passwords, mnemonics, or private
keys.
