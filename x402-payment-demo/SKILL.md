---
name: x402-payment-demo
description: "Demo of x402 payment protocol by fetching a protected resource on TRON. Triggers: 'demo x402-payment'"
version: 2.6.0
author: bankofai
metadata: {"clawdbot":{"emoji":"🖼️","triggers":["demo x402-payment", "show me x402 demo"]}}
tags: [x402, demo, payment, tron, image]
arguments:
  network:
    description: "Network to use. Current demo acceptance path is nile only."
    required: false
  server_url:
    description: "Demo server URL. Default: http://localhost:8010"
    required: false
---

# x402 Payment Demo Skill

This skill demonstrates the x402 payment protocol using the SDK v2 TypeScript demo stack on TRON.

Current acceptance scope:
- `tron:nile`
- `exact` scheme
- `tip712` and `permit2`

## Usage

Simply tell the Agent:
- "demo x402-payment"

## Prerequisites

The v2 TypeScript demo in `x402-demo/` must be configured and running locally.

Copy [`.env.sample`](/Users/bobo/code/x402/x402-demo/.env.sample) to `.env` inside `x402-demo/` and fill in:
- `TRON_CLIENT_PRIVATE_KEY`
- `TRON_FACILITATOR_PRIVATE_KEY`
- `PAY_TO_ADDRESS`

Then start the Nile facilitator and server:

```bash
# Terminal 1: Start facilitator
cd x402-demo && ./start.sh ts-facilitator

# Terminal 2: Start server
cd x402-demo && ./start.sh ts-server
```

## Workflow

1. Request the protected Nile endpoint:
   - `http://localhost:8010/protected-nile`
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

Expected result:
- initial request returns `402`
- replayed request returns `200`
- output includes a TRON settlement transaction hash
