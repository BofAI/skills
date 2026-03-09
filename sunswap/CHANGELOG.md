# Changelog

All notable changes to the SunSwap skill will be documented in this file.

## [2.0.3] - 2016-02-26
### Added
- add SunSwap V3 liquidity management skills

## [2.0.2] - 2016-02-25
### Added
- add SunSwap V2 liquidity management skills

## [2.0.1] - 2026-02-24
### Added
- get token price from sun price API

## [2.0.0] - 2026-02-13

### Changed - Major Architecture Shift

**Migration from MCP-based to Script-based Approach**

This version represents a fundamental shift in how the skill operates, moving from direct MCP tool calls to encapsulated scripts.

### Why the Change?

Direct MCP tool calls for DeFi operations proved error-prone due to:
- Complex parameter formatting (ABI structures, nested JSON)
- Multi-step workflows requiring precise state management
- High risk of "hallucination" errors in parameter construction
- Difficulty handling edge cases (version merging, fee arrays, etc.)

### What's New

**Added:**
- `scripts/balance.js` - Check token balances with automatic wallet detection
- `scripts/quote.js` - Get price quotes from SunSwap API
- `scripts/swap.js` - Execute swaps with flexible workflow options:
  - `--execute`: Full workflow (check → approve → swap)
  - `--check-only`: Balance and allowance check only
  - `--approve-only`: Approve tokens only
  - `--swap-only`: Execute swap only (assumes approved)
- `package.json` - Dependencies (tronweb, axios)
- Complete rewrite of `SKILL.md` with script-based instructions

**Removed:**
- `workflow/00_token_lookup.md` (MCP-based)
- `workflow/01_balance_check.md` (MCP-based)
- `workflow/02_approve.md` (MCP-based)
- `workflow/03_price_quote.md` (MCP-based)
- `workflow/04_execute_swap.md` (MCP-based)
- `examples/complete_swap_example.md` (MCP-based)
- `examples/swap_with_approve.md` (MCP-based)
- `examples/README.md` (outdated)
- `scripts/format_swap_params.js` (no longer needed - logic moved into swap.js)

### Migration Guide

**For AI Agents:**

Old approach (v1.x):
```bash
# Multiple MCP tool calls with complex parameter construction
mcp_mcp_server_tron_get_wallet_address()
mcp_mcp_server_tron_read_contract({...complex ABI...})
mcp_mcp_server_tron_write_contract({...complex args...})
```

New approach (v2.0):
```bash
# Simple script calls
node scripts/balance.js USDT nile
node scripts/quote.js TRX USDT 100 nile
node scripts/swap.js TRX USDT 100 nile --execute
```

**Benefits:**
- Reduced error rate (scripts handle complexity)
- Faster execution (fewer tool calls)
- Better user experience (clearer output)
- Easier debugging (script logs show exact issues)

### Breaking Changes

- All workflow files removed - use scripts instead
- All examples removed - scripts provide built-in examples
- `format_swap_params.js` removed - logic integrated into `swap.js`

### Compatibility

- Still works with same MCP server (mcp-server-tron)
- Same contract addresses and API endpoints
- Same token addresses in `resources/common_tokens.json`

## [1.0.0] - 2026-02-09

### Added
- Initial release with MCP-based workflow
- Step-by-step workflow documentation
- Complete swap examples
- Parameter formatting helper script
