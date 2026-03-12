---
name: x402-payment-demo
description: "Demo of x402 payment protocol by fetching a protected resource on TRON or optional BSC testnet. Triggers: 'demo x402-payment'"
version: 2.6.0
author: bankofai
metadata: {"clawdbot":{"emoji":"🖼️","triggers":["demo x402-payment", "show me x402 demo"]}}
tags: [x402, demo, payment, tron, bsc, image]
arguments:
  network:
    description: "Network to use. Supported: nile (default), bsc-testnet."
    required: false
  server_url:
    description: "Demo server URL. Default: http://localhost:8010"
    required: false
---

# x402 Payment Demo Skill

This skill demonstrates the x402 payment protocol using the SDK v2 TypeScript demo stack on TRON, with an optional BSC testnet endpoint.

Current acceptance scope:
- `tron:nile`
- `exact` scheme
- `tip712` and `permit2`
- optional `eip155:97`
- `exact` with EIP-3009 compatible test asset (`DHLU`)

## Usage

Simply tell the Agent:
- "demo x402-payment"

## Prerequisites

The v2 TypeScript demo in `x402-demo/` must be configured and running locally.

Copy [`.env.sample`](/Users/bobo/code/x402/x402-demo/.env.sample) to `.env` inside `x402-demo/` and fill in:
- `TRON_CLIENT_PRIVATE_KEY`
- `TRON_FACILITATOR_PRIVATE_KEY`
- `PAY_TO_ADDRESS`
- optional BSC values if you want the BSC endpoint:
  - `BSC_CLIENT_PRIVATE_KEY`
  - `BSC_FACILITATOR_PRIVATE_KEY`
  - `BSC_PAY_TO`
  - `BSC_TESTNET_RPC_URL`
  - `BSC_TEST_ASSET`

Before first run, bootstrap the local SDK packages used by the demo:

```bash
cd x402-demo && npm run bootstrap:local-sdk
```

Then start the TypeScript facilitator and server:

```bash
# Terminal 1: Start facilitator
cd x402-demo && ./start.sh ts-facilitator

# Terminal 2: Start server
cd x402-demo && ./start.sh ts-server
```

## Workflow

1. Request one of the protected endpoints:
   - TRON: `http://localhost:8010/protected-nile`
   - BSC: `http://localhost:8010/protected-bsc-testnet`
   - Multi-network: `http://localhost:8010/protected-multi`
2. Use the v2 TypeScript client in `x402-demo/ts/client.ts` to handle the payment flow:
   - receives `402 Payment Required`
    - creates an `exact` payment payload
    - replays the request with the payment payload
3. Confirm the server returns `200 OK` and a `payment-response` header containing the settlement transaction hash.

If the server starts before the facilitator is ready, restart the server once after the facilitator is up.

## Example

```bash
# Terminal 3: Run the v2 TypeScript client against the demo server
cd x402-demo && ./start.sh ts-client
```

For BSC testnet:

```bash
cd x402-demo && ENDPOINT=/protected-bsc-testnet ./start.sh ts-client
```

For a single endpoint that advertises both TRON and BSC, let the client choose with `PREFERRED_NETWORK`:

```bash
cd x402-demo && ENDPOINT=/protected-multi PREFERRED_NETWORK=tron:nile ./start.sh ts-client
```

```bash
cd x402-demo && ENDPOINT=/protected-multi PREFERRED_NETWORK=eip155:97 ./start.sh ts-client
```

Expected result:
- initial request returns `402`
- replayed request returns `200`
- output includes a settlement transaction hash
