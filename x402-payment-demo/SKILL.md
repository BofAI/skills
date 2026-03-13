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

This skill demonstrates the x402 payment protocol on the TRON and BSC networks.

## Usage

Simply tell the Agent:

- "demo x402-payment"
- "demo x402-payment on bsc-testnet"

## Workflow

1. **Request Resource**: When triggered, follow the instructions provided by the x402-payment skill to fetch the protected resource. Use Tron Nile by default:
   - Tron Nile (Default): `https://x402-demo.bankofai.io/protected-nile`
   - Tron Shasta: `https://x402-demo.bankofai.io/protected-shasta`
   - Tron Mainnet: `https://x402-demo.bankofai.io/protected-mainnet`
   - BSC Mainnet: `https://x402-demo.bankofai.io/protected-bsc-mainnet`
   - BSC Testnet: `https://x402-demo.bankofai.io/protected-bsc-testnet`
2. **Handle Payment**: Perform the payment and resource acquisition automatically as guided by the protocol (handling 402 Payment Required, signing permits, etc.).
3. **Display & Cleanup**: Once the image is retrieved, present / send it to the user. Immediately delete the local temporary file after the image has been displayed.
