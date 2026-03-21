# SunSwap Skill

Execute token swaps, manage liquidity, and query market data on SunSwap DEX via `sun-cli`.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![TRON](https://img.shields.io/badge/Blockchain-TRON-red)](https://tron.network/)

## Quick Start

**Instructions**: Read [SKILL.md](SKILL.md) for complete usage instructions.

## Approach

This skill uses **sun-cli** (`@bankofai/sun-cli`) — a unified CLI for SUN.IO / SunSwap on TRON. All swap, liquidity, price, pool, and position operations are handled through `sun` commands with `--json` output for AI agent consumption.

## Files

- **[SKILL.md](SKILL.md)** - Complete skill documentation with all commands and workflows
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

## Prerequisites

```bash
npm install -g @bankofai/sun-cli
```

## Networks

| Network | Description |
|---------|-------------|
| **mainnet** | TRON mainnet (default) |
| **nile** | TRON Nile testnet |
| **shasta** | TRON Shasta testnet |

## Usage Examples

### Check Wallet
```bash
sun --json wallet address
sun --json wallet balances
```

### Get Price
```bash
sun --json price TRX
```

### Swap Tokens
```bash
sun --json swap:quote TRX USDT 100000000
sun --json --yes swap TRX USDT 100000000 --slippage 0.005
```

### Manage Liquidity
```bash
# V2
sun --json --yes liquidity v2:add --token-a TRX --token-b USDT --amount-a 1000000

# V3
sun --json --yes liquidity v3:mint --token0 TRX --token1 USDT --fee 3000 --amount0 1000000

# V4
sun --json --yes liquidity v4:mint --token0 TRX --token1 USDT --amount0 1000000
```

### Query Pools
```bash
sun --json pool top-apy --page-size 10
sun --json pool search "TRX USDT"
```

### Check Positions
```bash
sun --json position list --owner TAddress
```

## Dependencies

- `@bankofai/sun-cli` (installed globally)

## Version

3.0.0 (2026-03-15) - sun-cli based approach

See [CHANGELOG.md](CHANGELOG.md) for migration notes.

## License

MIT - see [LICENSE](../../LICENSE) for details
