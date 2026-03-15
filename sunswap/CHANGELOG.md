# Changelog

All notable changes to the SunSwap skill will be documented in this file.

## [3.0.0] - 2026-03-15

### Changed - Major Architecture Shift

**Migration from script-based to sun-cli approach**

This version replaces all custom Node.js scripts with `sun-cli` (`@bankofai/sun-cli`), a unified CLI for SUN.IO / SunSwap on TRON.

### Why the Change?

The script-based approach (v2.x) required maintaining separate scripts for each operation (balance, quote, swap, liquidity, position), each with its own dependencies and token resolution logic. `sun-cli` consolidates everything into a single tool with consistent flags, built-in symbol resolution, and structured output modes.

### What's New

**Added:**
- Full coverage of `sun-cli` commands in SKILL.md: wallet, price, swap, quote, liquidity (V2/V3/V4), pool discovery, token search, position management, pair info, protocol analytics, farm, transaction scan, and generic contract calls
- V4 liquidity management (new in sun-cli, not available in v2.x scripts)
- Pool discovery and analytics commands
- Protocol-level metrics
- Farm inspection
- Transaction scanning
- `--dry-run` support for safe simulation of write operations

**Removed:**
- `scripts/` directory (balance.js, quote.js, price.js, swap.js, liquidity.js, position.js, utils.js, and all test files)
- `resources/` directory (common_tokens.json, sunswap_contracts.json, liquidity_manager_contracts.json)
- `package.json` (no local dependencies needed — sun-cli is installed globally)

### Migration Guide

**For AI Agents:**

Old approach (v2.x):
```bash
node scripts/balance.js USDT --network nile
node scripts/quote.js TRX USDT 100
node scripts/swap.js TRX USDT 100 --execute
node scripts/liquidity.js add TRX USDT 100 15 --execute
node scripts/position.js add TRX USDT 100 15 --fee 3000 --tick-lower -60 --tick-upper 60 --execute
```

New approach (v3.0):
```bash
sun --json wallet balances --network nile
sun --json swap:quote TRX USDT 100000000
sun --json --yes swap TRX USDT 100000000
sun --json --yes liquidity v2:add --token-a TRX --token-b USDT --amount-a 100000000
sun --json --yes liquidity v3:mint --token0 TRX --token1 USDT --fee 3000 --tick-lower -60 --tick-upper 60 --amount0 100000000
```

**Key differences:**
- Amounts are now in sun (smallest unit), not human-readable token units
- `--execute` / `--check-only` / `--approve-only` flags replaced by `--dry-run` and `--yes`
- Token approval is handled automatically by sun-cli
- All output uses `--json` for structured JSON

### Breaking Changes

- All scripts removed — use `sun` CLI commands instead
- All resource files removed — sun-cli has built-in token and contract resolution
- `package.json` removed — no local `npm install` needed
- Amount format changed to sun (smallest unit) instead of human-readable

## [2.0.3] - 2026-02-26
### Added
- SunSwap V3 liquidity management skills

## [2.0.2] - 2026-02-25
### Added
- SunSwap V2 liquidity management skills

## [2.0.1] - 2026-02-24
### Added
- Get token price from Sun price API

## [2.0.0] - 2026-02-13

### Changed - Major Architecture Shift

**Migration from MCP-based to Script-based Approach**

### What's New

**Added:**
- `scripts/balance.js` - Check token balances
- `scripts/quote.js` - Get price quotes
- `scripts/swap.js` - Execute swaps with flexible workflow
- `package.json` - Dependencies (tronweb, axios)
- Complete rewrite of `SKILL.md` with script-based instructions

**Removed:**
- All MCP-based workflow files
- All MCP-based example files
- `format_swap_params.js`

## [1.0.0] - 2026-02-09

### Added
- Initial release with MCP-based workflow
- Step-by-step workflow documentation
- Complete swap examples
- Parameter formatting helper script
