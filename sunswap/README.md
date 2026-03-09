# SunSwap Skill

Execute token swaps on SunSwap DEX using Smart Router for optimal routing across V1/V2/V3/PSM pools.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![TRON](https://img.shields.io/badge/Blockchain-TRON-red)](https://tron.network/)

## Quick Start

**Instructions**: Read [SKILL.md](SKILL.md) for complete usage instructions.

## Approach

This skill uses **script-based execution** instead of direct MCP tool calls. Scripts handle complex parameter formatting, ABI management, and multi-step workflows, reducing AI errors and ensuring reliable execution.

## Files

- **[SKILL.md](SKILL.md)** - Complete skill documentation
- **[scripts/balance.js](scripts/balance.js)** - Check token balances
- **[scripts/quote.js](scripts/quote.js)** - Get price quotes
- **[scripts/price.js](scripts/price.js)** - Get token spot price via Sun Open API
- **[scripts/swap.js](scripts/swap.js)** - Execute swaps (with flexible workflow options)
- **[scripts/liquidity.js](scripts/liquidity.js)** - Add/remove liquidity on SunSwap V2 pools
- **[scripts/position.js](scripts/position.js)** - Manage V3 concentrated liquidity positions (add/remove/collect)
- **[resources/sunswap_contracts.json](resources/sunswap_contracts.json)** - Contract addresses and API endpoints
- **[resources/common_tokens.json](resources/common_tokens.json)** - Token addresses and decimals
- **[resources/liquidity_manager_contracts.json](resources/liquidity_manager_contracts.json)** - SunSwap V2 Router/Factory addresses and ABIs

## Networks

| Network | Smart Router | API Endpoint |
|---------|-------------|--------------|
| **Mainnet** | `TGnC7LMji8hBpyvZt1TTEJhVpAZ5HFyJ3r` | `https://rot.endjgfsv.link/swap/router` |
| **Nile** | `TMEkn7zwGJvJsRoEkiTKfGRGZS2yMdVmu3` | `https://tnrouter.endjgfsv.link/swap/router` |

## Installation

```bash
cd skills/sunswap
npm install
```

## Usage Examples

### Check Balance
```bash
node scripts/balance.js USDT nile
```

### Get Quote
```bash
node scripts/quote.js TRX USDT 100 nile
```

### Get Token Price (Sun Open API)
```bash
# By symbol (mainnet)
node scripts/price.js TRX

# By contract address (mainnet TRX)
node scripts/price.js T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb

# Explicit currency (defaults to USD)
node scripts/price.js USDT --currency USD
```

### Add Liquidity (SunSwap V2)
```bash
# Dry-run (shows optimal amounts, approvals needed)
node scripts/liquidity.js add TRX USDT 100 15 --network nile

# Execute
node scripts/liquidity.js add TRX USDT 100 15 --network nile --execute

# Two TRC20 tokens
node scripts/liquidity.js add USDT USDC 100 100 --network nile --execute
```

### Remove Liquidity (SunSwap V2)
```bash
# Dry-run
node scripts/liquidity.js remove TRX USDT 5.5 --network nile

# Execute
node scripts/liquidity.js remove TRX USDT 5.5 --network nile --execute
```

### V3 Position Management (SunSwap V3)
```bash
# List positions
node scripts/position.js positions --network nile

# Add position (3-step workflow)
node scripts/position.js add TRX USDT 100 15 --fee 3000 --tick-lower -60 --tick-upper 60 --check-only
node scripts/position.js add TRX USDT 100 15 --fee 3000 --tick-lower -60 --tick-upper 60 --approve-only --execute
node scripts/position.js add TRX USDT 100 15 --fee 3000 --tick-lower -60 --tick-upper 60 --execute

# Remove 50% of position
node scripts/position.js remove --position-id 12345 --percent 50 --execute

# Collect fees
node scripts/position.js collect --position-id 12345 --execute
```

### Execute Swap (Full Workflow)
```bash
node scripts/swap.js TRX USDT 100 nile --execute
```

### Execute Swap (Step-by-Step)
```bash
# 1. Check only (balance + allowance)
node scripts/swap.js TRX USDT 100 nile --check-only

# 2. Approve only (if needed)
node scripts/swap.js TRX USDT 100 nile --approve-only

# 3. Swap only (assumes already approved)
node scripts/swap.js TRX USDT 100 nile --swap-only
```

## Dependencies

- Node.js 14+
- tronweb
- axios

## Tests

```bash
cd skills/sunswap

# Price script tests (network call to Sun Open API)
npm run test:price

# Liquidity script tests (pure-function + optional on-chain read)
npm run test:liquidity

# V3 Position script tests (pure-function: V3 math, tick alignment, etc.)
npm run test:position
```

## Version

2.0.0 (2026-02-13) - Script-based approach

See [CHANGELOG.md](CHANGELOG.md) for migration notes.

## License

MIT - see [LICENSE](../../LICENSE) for details
