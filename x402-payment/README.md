# x402 Payment Skill

Invoke x402-protected APIs and agent resources with automatic payment handling on TRON and EVM networks.

## Quick Start

```bash
cd skills/x402-payment
npm install
npx tsx src/x402_invoke.ts --check
```

## What It Supports

- TRON payments on `tron:nile`, `tron:mainnet`, and `tron:shasta`
- EVM payments on `eip155:56` (BSC mainnet) and `eip155:97` (BSC testnet)
- Automatic 402 challenge handling through `@bankofai/x402-fetch`
- TRON `exact`/Permit2 and `exact_gasfree` through `@bankofai/x402-tron`
- EVM `exact` through `@bankofai/x402-evm`

This skill is aligned with the modular BankofAI x402 SDK `1.0.0` packages.

> **Breaking changes vs 1.5.x:** the `exact_permit` scheme (removed in SDK 1.0) and the `eip155:*` wildcard (EVM chains other than BSC) are no longer supported.

## Files

- [SKILL.md](SKILL.md) - Full skill instructions and operator guidance
- [src/x402_invoke.ts](src/x402_invoke.ts) - Main CLI entrypoint for invoking x402-protected endpoints
- [package.json](package.json) - Skill runtime metadata and dependencies

## Requirements

- Node.js 20+
- Agent Wallet configured for TRON and/or EVM signing
- Optional `TRON_GRID_API_KEY` for TRON mainnet reliability
- Optional `EVM_RPC_URL_56` / `EVM_RPC_URL_97` for custom BSC mainnet/testnet RPC endpoints
- Optional `X402_DEBUG=1` for expanded debug output

This skill uses `agent-wallet` as its signing source. It does not read raw private keys from shared MCP config files.

## Usage Examples

### Check Wallet Resolution

```bash
npx tsx src/x402_invoke.ts --check
```

### Call a Public Endpoint

```bash
npx tsx src/x402_invoke.ts --url https://x402-demo.bankofai.io/
```

### Pay for a TRON Endpoint

```bash
npx tsx src/x402_invoke.ts \
  --url https://x402-demo.bankofai.io/protected-nile \
  --network nile
```

### Query GasFree Account Info

```bash
npx tsx src/x402_invoke.ts --gasfree-info --network nile
```

### Local Coinbase-Compatible BSC Demo

```bash
npx tsx src/x402_invoke.ts \
  --url http://127.0.0.1:8012/protected-bsc-testnet-coinbase \
  --network bsc-testnet
```

## Notes

- Wallet resolution uses Agent Wallet and the SDK 1.0 signer adapters; the skill never reads raw private keys.
- The tool decodes `payment-response` headers and prints settlement details to stderr for easier verification.
- For local BSC exact compatibility tests, the demo route is `/protected-bsc-testnet-coinbase`.

## License

MIT
