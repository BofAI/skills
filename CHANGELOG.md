# Changelog

## [1.4.0] - 2026-03-11

### Features
- **[Skill] x402-payment GasFree**: Gasless TRC20 payments via GasFree protocol (`exact_gasfree` scheme). New CLI commands `--gasfree-info` and `--gasfree-activate`. (#11)
- **[Skill] AINFT**: New skill for AINFT merchant agent — check balances and orders. (#13)
- **[Skill] SunSwap Liquidity**: V2/V3 liquidity management (add/remove/collect), position queries, and token price scripts. (#12)
- **[Skill] 8004 Search**: Agent search via search-service with multi-chain support.

### Improvements
- **x402-payment**: Removed bundled `dist/` (~103K lines), run TypeScript directly via `npx tsx`. Upgraded `@bankofai/x402` to 0.4.1.
- **x402-payment**: Extracted handler functions (`handleCheck`, `handleGasFreeInfo`, `handleGasFreeActivate`), replaced hardcoded 30s sleep with tx confirmation polling.
- **x402-payment**: Credential resolution from env, `x402-config.json`, and `mcporter.json` with `.trim()` whitespace guard.
- **README**: Updated repo structure, x402-payment description, and GitHub org URLs.

### Bug Fixes
- Fixed GitHub org URL (`bankofai` → `BofAI`) across README and install scripts.
- Fixed `gaFreeTxHash` typo → `gasFreeTxHash` in x402-payment output.

## [1.0.0] - 2026-02-09

### ✨ Features
- **[Skill] SunSwap DEX**: Complete workflow for token swaps with slippage protection and Smart Router support.
- **[Skill] x402 Payment**: Seamless TRC20 payments for AI agent APIs with automatic 402 error handling.
- **[Skill] x402 Demo**: Reference implementation for validating payment protocols.
- **[Gas] Cost Optimization**: Implemented `MaxUint160` infinite approvals to minimize long-term transaction costs.
- **[Documentation] Standardized Guides**: `AGENTS.md` and `README.md`.

### Bug Fixes
- Standardized project structure and naming conventions.
