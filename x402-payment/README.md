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
- EVM payments on `eip155:*`, including BSC testnet and mainnet flows
- Automatic 402 challenge handling through `X402Client` and `X402FetchClient`
- Optional GasFree support for TRON when the upstream x402 library exposes `exact_gasfree`

This skill is aligned with `@bankofai/x402@0.5.9`, including Exact V2-compatible payload generation.

## Files

- [SKILL.md](SKILL.md) - Full skill instructions and operator guidance
- [src/x402_invoke.ts](src/x402_invoke.ts) - Main CLI entrypoint for invoking x402-protected endpoints
- [package.json](package.json) - Skill runtime metadata and dependencies

## Requirements

- Node.js 20+
- Agent Wallet configured for TRON and/or EVM signing
- Optional `TRON_GRID_API_KEY` for TRON mainnet reliability
- Optional `X402_DEBUG=1` for expanded debug output

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

- Wallet resolution uses Agent Wallet (`TronClientSigner.create()` / `EvmClientSigner.create()`).
- The tool decodes `payment-response` headers and prints settlement details to stderr for easier verification.
- For local BSC exact compatibility tests, the demo route is `/protected-bsc-testnet-coinbase`.

## License

MIT
