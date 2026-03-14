---
name: x402-payment
description: "Pay for x402-enabled endpoints with the v2 SDK on TRON or BSC. Triggers: 'pay with x402', 'invoke paid endpoint'."
version: 2.6.0
author: bankofai
homepage: https://bankofai.io
tags: [x402, payment, tron, bsc, exact, eip3009, permit2, skill]
requires_tools: [x402]
arguments:
  url:
    description: "Base URL of the agent (for --entrypoint) or a direct endpoint URL."
    required: true
  entrypoint:
    description: "Entrypoint name to invoke, for example 'chat' or 'search'."
    required: false
  input:
    description: "JSON input object or raw string payload."
    required: false
  method:
    description: "HTTP method when calling a direct URL. Default: GET."
    required: false
  network:
    description: "Preferred network. Supported: nile, mainnet, shasta, bsc-testnet, bsc."
    required: false
  asset:
    description: "Preferred asset or token address, for example USDT, USDD, 0x..., or T...."
    required: false
  token:
    description: "Alias of --asset."
    required: false
  pair:
    description: "Preferred network+asset pair, for example tron:nile:USDT or eip155:97/0x..."
    required: false
---

# x402 Payment Skill

This skill uses the **v2 SDK** to invoke x402-protected HTTP endpoints with automatic payment handling.

Supported payment paths:
- `tron:*` with `exact`
  - `eip3009`
  - `permit2`
- `eip155:56`
- `eip155:97`

## Prerequisites

Before first use, install the local v2 SDK packages:

```bash
cd skills/x402-payment
npm run bootstrap:local-sdk
```

Configure wallet keys with environment variables, `x402-config.json`, or `~/.x402-config.json`.

- TRON:
  - `TRON_PRIVATE_KEY`
  - optional `TRON_GRID_API_KEY`
- EVM:
  - `EVM_PRIVATE_KEY` or `ETH_PRIVATE_KEY`
  - optional `BSC_MAINNET_RPC_URL`
  - optional `BSC_TESTNET_RPC_URL`

## Verification

Check that the skill can discover your local wallet configuration:

```bash
x402 status
```

Show currently configured native balances:

```bash
x402 balance
```

If a Permit2 payment fails because the token has not approved Permit2 yet, approve once first:

```bash
x402 approve https://tn-x402-demo.bankofai.io/protected-nile --network nile --asset USDT
```

## Usage

### Coinbase-style CLI

```bash
x402 pay \
  https://tn-x402-demo.bankofai.io/protected-nile \
  --network nile \
  --asset USDT
```

### Common options

```bash
x402 pay <url> \
  -X POST \
  -d '{"prompt":"hello"}' \
  -q '{"verbose":"true"}' \
  -h '{"X-App":"demo"}' \
  --max-amount 100000 \
  --network bsc-testnet
```

### Pair selection

```bash
x402 pay \
  https://tn-x402-demo.bankofai.io/protected-nile \
  --pair tron:nile:USDT
```

### Permit2 approval

`x402 approve` fetches the endpoint's `402 Payment Required` response, applies the same selection rules as `x402 pay`, and sends a Permit2 approval transaction for the selected asset.

```bash
x402 approve \
  https://tn-x402-demo.bankofai.io/protected-bsc-testnet \
  --network bsc-testnet \
  --asset USDT
```

### Hosted demo endpoints

The hosted demo URLs currently used by the companion `x402-payment-demo` skill are:

- `https://tn-x402-demo.bankofai.io/protected-nile`
- `https://tn-x402-demo.bankofai.io/protected-bsc-testnet`
- `https://tn-x402-demo.bankofai.io/protected-multi`

### Local demo endpoints

If you are running `x402-demo` locally, this skill can call it directly:

- `http://127.0.0.1:8000/protected-nile`
- `http://127.0.0.1:8000/protected-bsc-testnet`
- `http://127.0.0.1:8000/protected-multi`

Replace `8000` with your local server port if you started the demo on a different port.

## Behavior

1. Make the initial HTTP request.
2. If the endpoint returns `402 Payment Required`, automatically select a matching payment option.
   - priority: `network + pair/asset`
   - then `network`
   - then first available option
   - if `--max-amount` is set, requirements above that atomic-unit amount are filtered out
3. Create the payment payload using the v2 SDK.
4. Retry the request with payment headers.
5. Print the final HTTP response as JSON.

If the selected payment option uses `permit2` and allowance is missing, run `x402 approve` once with the same URL/network/asset selectors, then retry `x402 pay`.

If a response returns binary data, it is written to a temporary file and the file path is returned.

That includes the current `x402-demo` protected image flow, which returns `protected.png` after successful payment.

## Notes

- This skill is now aligned to the **v2 exact** flow only.
- Legacy `exact_permit` and `exact_gasfree` behavior is not part of this skill anymore.
- For the hosted demo flow, use [x402-payment-demo](/Users/bobo/code/x402/skills/x402-payment-demo/SKILL.md).
