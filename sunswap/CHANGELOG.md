# Changelog

All notable changes to the SunSwap skill will be documented in this file.

## [3.0.1] - 2026-03-18

### Fixed

Based on test report (134 cases, 7 failures), added documentation for CLI-level behaviors that require agent-side workarounds:

- **Added "Agent Pre-Validation Checklist" section**: Mandatory checks before executing write operations (balance, same-token swap, fee tier, tick alignment, network, tx scan type)
- **Added "Known Limitations" table**: Documents 7 CLI behaviors where `--dry-run` or invalid inputs don't produce errors
- **Fixed `pair info` examples**: `--token` requires contract address, not symbol (TC_PAR_002)
- **Updated V3 fee tier table**: Added "Full Range Ticks" column and validation warnings (TC_V3L_004, TC_V3L_005)
- **Updated recommended swap workflow**: Now includes balance pre-check step and same-token validation (TC_SWP_006, TC_SCN_005)
- **Updated V3 liquidity workflow**: Now includes fee/tick validation step before dry-run (TC_V3L_004, TC_V3L_005)
- **Documented `--dry-run` limitations**: Clarified that dry-run only builds transaction preview, does NOT validate balances, fees, ticks, or same-token swaps (TC_SWP_006, TC_V2L_007, TC_V3L_004, TC_V3L_005, TC_SCN_005)
- **Documented `--network` fallback behavior**: Invalid network names silently fall back to mainnet (TC_GEN_006)
- **Documented `--type` fallback behavior**: Invalid tx scan types return empty results without error (TC_TXS_004)
- **Strengthened security rules**: Replaced "Use Dry-Run for High-Value Operations" with "Validate Inputs Before Execution" + "Use Quote + Balance Check"

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
