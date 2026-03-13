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

1. **Resolve Endpoint**: Use `https://x402-demo.bankofai.io` and append the network path:
   - Tron Nile (default): `/protected-nile`
   - BSC Testnet: `/protected-bsc-testnet`
   - Multi-network: `/protected-multi`
2. **Invoke Payment Flow**: Use the [x402-payment](/Users/bobo/code/x402/skills/x402-payment/SKILL.md) skill against the resolved URL.
3. **Default Selection**: If `network` is omitted, use `nile`.
4. **Return Result**: Return the final paid response to the user. If the response is binary, report the temporary file path returned by the payment skill.

## Hosted endpoints

- Tron Nile (Default): `https://x402-demo.bankofai.io/protected-nile`
- BSC Testnet: `https://x402-demo.bankofai.io/protected-bsc-testnet`
- Multi-network: `https://x402-demo.bankofai.io/protected-multi`

## Examples

```bash
x402 pay https://x402-demo.bankofai.io/protected-nile --network nile
```

```bash
x402 pay https://x402-demo.bankofai.io/protected-bsc-testnet --network bsc-testnet
```
