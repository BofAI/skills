# SunPump Skill

Create and trade meme tokens on **SunPump** and query token info, rankings, holders, portfolios, and trade history via `sun-cli`.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![TRON](https://img.shields.io/badge/Blockchain-TRON-red)](https://tron.network/)

## Quick Start

**Instructions**: Read [SKILL.md](SKILL.md) for complete usage instructions.

## Approach

This skill uses **sun-cli** (`@bankofai/sun-cli`) — a unified CLI for SUN.IO / SunSwap / SunPump on TRON. Token creation goes through the SunPump agent endpoint (`sun sunpump launch` — server-side, no wallet). Trading auto-routes by token state: pre-launch (bonding curve) tokens go through `sun sunpump buy/sell`, post-launch (migrated to DEX) tokens go through `sun swap`. All SunPump data is read through the `sun sunpump *` subcommands with `--json` output for AI agent consumption.

## Files

- **[SKILL.md](SKILL.md)** - Complete skill documentation

## Install

Two pieces — the skill (loaded by Claude Code / Cursor / Codex) and the runtime CLI it shells out to.

### 1. Install this skill

```bash
npx skills add BofAI/skills 
```


### 2. Install the runtime CLI

```bash
npm install -g @bankofai/sun-cli@^1.2.1
```

`@bankofai/sun-cli >= 1.2.1` is required (earlier versions lack `sun sunpump launch`; < 1.2.0 also lack `sun sunpump buy/sell/state`). The skills CLI does **not** auto-install npm dependencies.

### 3. Configure a wallet (only for trading commands)

A wallet (`TRON_PRIVATE_KEY`, `TRON_MNEMONIC`, or `AGENT_WALLET_PASSWORD`) is required only for `sun swap` / `sun sunpump buy` / `sun sunpump sell`. All read endpoints work without one, and so does token creation (`sun sunpump launch` — the platform signs server-side).


## Network

SunPump is **mainnet only**: `https://api-v2.sunpump.meme/pump-api`. The CLI rejects
any non-mainnet `--network` value (the testnet host is internal-only and not publicly
reachable). Drop `--network` or pass `--network mainnet`.

## Feature Summary

| # | Feature | Command |
|---|---------|---------|
| 1 | Create (launch) a token | `sun --json --yes sunpump launch --name <n> --symbol <s> --description <d> --image <path>` |
| 2 | Post-launch buy / sell | `sun --json --yes swap <tokenIn> <tokenOut> <amount>` |
| 3 | Pre-launch buy / sell | `sun --json --yes sunpump buy <addr> --trx <n>` · `sun --json --yes sunpump sell <addr> --amount <n>` |
| 4 | Token state (route picker) | `sun --json sunpump state <contractAddress>` |
| 5 | User position check | `sun --json sunpump portfolio <walletAddress>` |
| 6 | Trade history | `sun --json sunpump tx user <walletAddress> --size 20` |
| 7 | Token info | `sun --json sunpump token get <contractAddress>` |
| 8 | Ranking | `sun --json sunpump token ranking --type MARKET_CAP --size 10` |
| 9 | Top holders | `sun --json sunpump token holders <contractAddress> --size 20` |

Ranking types: `MARKET_CAP`, `VOLUME_24H`, `PRICE_CHANGE_24H`.

State values: `0 NOT_EXIST`, `1 TRADING`, `2 READY_TO_LAUNCH`, `3 LAUNCHED`.

## Usage Examples

### Create a new meme token (no wallet needed — server-side creation)
```bash
sun --json sunpump token search MEME                       # check for symbol collisions
sun --json --yes --dry-run sunpump launch --name "My Meme" --symbol MEME \
  --description "The dankest meme on TRON" --image ./logo.png   # preview payload
sun --json --yes sunpump launch --name "My Meme" --symbol MEME \
  --description "The dankest meme on TRON" --image ./logo.png   # create (irreversible)
sun --json sunpump state <contractAddress>                 # expect 1 (TRADING)
```
Always pass `--image` — launches without a logo often fail with `Invoke third part error`.

### Buy a meme token (auto-routes pre/post-launch)
```bash
sun --json sunpump state TXYZ...                          # decide trade path
sun --json sunpump token get TXYZ...                      # show metadata + holders

# Pre-launch (state == 1 or 2):
sun --json sunpump quote-buy TXYZ... --trx 10
sun --json --yes sunpump buy TXYZ... --trx 10

# Post-launch (state == 3):
sun --json swap:quote TRX TXYZ... 100000000
sun --json --yes swap TRX TXYZ... 100000000 --slippage 0.01
```

### Sell a position (auto-routes pre/post-launch)
```bash
sun --json sunpump portfolio T... --min-trx 1 --size 50
sun --json sunpump state TXYZ...

# Pre-launch:
sun --json --yes sunpump sell TXYZ... --amount 1000 --decimals 18

# Post-launch:
sun --json --yes swap TXYZ... TRX <amount> --slippage 0.02
```

### Research a token
```bash
sun --json sunpump token ranking --type PRICE_CHANGE_24H --size 10
sun --json sunpump token get TXYZ...
sun --json sunpump token holders TXYZ... --size 20
```

### Audit a wallet
```bash
sun --json sunpump portfolio T... --sort valueInTrx,desc --size 50
sun --json sunpump tx user T... --size 20
```

## Dependencies

- `@bankofai/sun-cli` (installed globally)

## Version

1.3.1 (2026-06-08) — docs: clarify `sun sunpump launch` is mainnet-only (sun-cli dropped SunPump nile support again); document that `--dry-run` skips the mainnet check

1.3.0 (2026-06-04) — adds token creation via `sun sunpump launch` (server-side `POST /ai/agentTokenLaunch`, no wallet needed); requires sun-cli ≥ 1.2.1

1.2.0 (2026-05-22) — breaking: drops nile testnet (internal-only host); upstream `sun sunpump` API surface also trimmed (no more `home/kline/red-packet/campaign/referral/admin-summary/quota/tx ticker`)

1.1.1 (2026-05-21) — docs: install via `npx skills add`, pin sun-cli ≥ 1.2.0

1.1.0 (2026-05-20) — adds pre-launch bonding-curve trading (`sun sunpump buy/sell/quote-buy/quote-sell/state`)

1.0.0 (2026-05-20) — initial release


## License

MIT - see [LICENSE](../LICENSE) for details.
