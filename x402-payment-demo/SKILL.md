---
name: x402-payment-demo
description: "Demo of x402 payment protocol against hosted x402 demo endpoints on TRON or BSC. Triggers: 'demo x402-payment'"
version: 2.6.0
author: bankofai
metadata: {"clawdbot":{"emoji":"🖼️","triggers":["demo x402-payment", "show me x402 demo"]}}
tags: [x402, demo, payment, tron, bsc, image]
arguments:
  network:
    description: "Network to use. Supported: nile (default), bsc-testnet, multi."
    required: false
---

# x402 Payment Demo Skill

This skill demonstrates the x402 payment protocol on the TRON and BSC networks against the hosted `x402-demo` service.

## Usage

Simply tell the Agent:

- "demo x402-payment"
- "demo x402-payment on bsc-testnet"

## Workflow

1. **Resolve Endpoint**: Use `https://tn-x402-demo.bankofai.io` and append the network path:
   - Tron Nile (default): `/protected-nile`
   - BSC Testnet: `/protected-bsc-testnet`
   - Multi-network: `/protected-multi`
2. **Invoke Payment Flow**: Use the installed local launcher from [x402-payment](/Users/bobo/code/x402/skills/x402-payment/SKILL.md):

```bash
node "$HOME/.openclaw/skills/x402-payment/bin/x402.js" pay <resolved-url> --network <network>
```

3. **Default Selection**: If `network` is omitted, use `nile`.
4. **Return Result**: Return the final paid response to the user. If the response is binary, report the temporary file path returned by the payment skill.

If payment fails because Permit2 allowance is missing, call:

```bash
node "$HOME/.openclaw/skills/x402-payment/bin/x402.js" approve <resolved-url> --network <network>
```

Then retry the demo payment once.

## Hosted endpoints

- Tron Nile (Default): `https://tn-x402-demo.bankofai.io/protected-nile`
- BSC Testnet: `https://tn-x402-demo.bankofai.io/protected-bsc-testnet`
- Multi-network: `https://tn-x402-demo.bankofai.io/protected-multi`

The BSC hosted demo accepts public BSC testnet stablecoins:

- `USDT`
- `USDC`

## Examples

```bash
node "$HOME/.openclaw/skills/x402-payment/bin/x402.js" pay https://tn-x402-demo.bankofai.io/protected-nile --network nile
```

```bash
node "$HOME/.openclaw/skills/x402-payment/bin/x402.js" pay https://tn-x402-demo.bankofai.io/protected-bsc-testnet --network bsc-testnet
```
