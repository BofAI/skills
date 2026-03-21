# Changelog

All notable changes to the SunSwap skill will be documented in this file.

## [3.2.0] - 2026-03-20

### Breaking Changes
- Removed legacy scripts/resources. Replace:
  - `scripts/swap.js` → `sun --json --yes swap ...`
  - `scripts/balance.js` → `sun --json wallet balances`
  - `scripts/quote.js` → `sun --json quote ...`
  - `scripts/price.js` → `sun --json price <TOKEN>`
  - `scripts/liquidity.js` → `sun --json liquidity ...`
  - `scripts/position.js` → `sun --json position ...`

### Fixed — Documentation Issues from Test Report (134 cases, 18 failures)

Full test coverage (134/134 cases executed, 116 passed, 18 failed) revealed documentation gaps
and missing guidance in SKILL.md. Changes address the following failure categories:

**Wallet & Token Filtering (TC_WLT_004, TC_WLT_007)**
- Added documentation that `--tokens` filter on `wallet balances` only accepts contract addresses,
  not symbols. Passing `TRX,USDT` returns `Invalid contract address provided`.
- Added `AGENT_WALLET_PASSWORD` troubleshooting: requires `~/.agent-wallet` directory to be
  initialized. Documented fallback to `TRON_PRIVATE_KEY` or `TRON_MNEMONIC`.

**Contract Read BigInt (TC_CTR_002)**
- Added BigInt serialization warning to Known Limitations: `contract read` functions returning
  large integers (e.g. `totalSupply`) may crash JSON output.

**Pair Info (TC_PAR_002, TC_PAR_003)**
- Strengthened warning that `pair info --token` only accepts contract addresses. Symbols will
  fail or return unexpected results.

**V3 Parameter Validation (TC_V3L_004, TC_V3L_005, TC_V3L_010)**
- Added pre-validation step for V3/V4 position operations: verify token-id exists via
  `position list` before calling `increase`/`decrease`/`collect`.
- Added known limitation for misleading error when token-id does not exist.

**Security & Confirmation Workflow (TC_SEC_004, TC_SEC_005)**
- Rewrote "Confirm Before Write Operations" section to enforce a strict preview-then-execute
  protocol: agents must get a quote or dry-run, display it to the user, and obtain explicit
  confirmation before passing `--yes`.

**Testnet Execution (TC_SWP_002)**
- Added troubleshooting guidance for testnet bandwidth/energy failures.

### Known Limitations Added

| Issue | Commands |
|-------|----------|
| `--tokens` needs contract addresses | `wallet balances` |
| BigInt JSON serialization crash | `contract read` |
| Misleading V3 token-id errors | `v3:increase/decrease/collect` |
| `AGENT_WALLET_PASSWORD` needs store | `wallet address` |
| Testnet resource requirements | All write commands on nile/shasta |

## [3.1.0] - 2026-03-20

### Fixed — Command Format Compatibility

Test report (134 cases, 34 failures) revealed that the test framework cannot parse multi-line commands
or angle-bracket placeholders in bash code blocks. All 34 failures fell into two categories:

**Category 1: Multi-line `\` continuations (28 failures)**
The test parser extracted only fragments when commands spanned multiple lines with `\`.
Affected: V2 add/remove, V3 mint/increase/decrease/collect, V4 mint/increase/decrease, contract send,
swap with options, position filter, fields filter.

**Category 2: Angle-bracket placeholders interpreted as shell I/O redirection (3 failures)**
Placeholders like `<raw>`, `<validAddr>`, `<func>` caused `/bin/sh: cannot open xxx: No such file`.
Affected: V4 decrease (`--liquidity <raw>`), contract read/send (`<address>`, `<func>`).

### Changes

- **Flattened all commands to single lines**: Removed every `\` continuation. Every bash code block
  now contains exactly one complete, executable command per line.
- **Replaced all angle-bracket placeholders with concrete values**: `<token>` → `TRX`/`USDT`,
  `<id>` → `123`, `<amount>` → `1000000`, `<address>` → real TRON addresses,
  `<functionName>` → `name`/`balanceOf`/`approve`, `<raw>` → `1000`, `<poolAddress>` → real pool address.
- **Moved parameter syntax descriptions to plain text**: Template signatures with `[optional]` brackets
  and `<placeholder>` values are now in markdown paragraphs, not bash code blocks.
- **Split multi-command code blocks into separate blocks**: Each bash block contains one command,
  making extraction unambiguous.
- **Used real addresses in examples**: `TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW` (wallet),
  `TSUUVjysXV8YqHytSNjfkNXnnB49QDvZpx` (pool), `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t` (USDT).
- **Added runnable security verification command** for TC_SEC_001/002 (output not containing private keys).

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
