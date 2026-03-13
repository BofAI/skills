---
name: x402-payment-demo
description: "Demo of x402 payment protocol by fetching a protected image on TRON or BSC. Triggers: 'demo x402-payment'"
version: 1.1.0
author: bankofai
metadata: {"clawdbot":{"emoji":"🖼️","triggers":["demo x402-payment", "show me x402 demo"]}}
tags: [x402, demo, payment, tron, bsc, image]
arguments:
  network:
    description: "Network to use (nile, shasta, mainnet, bsc, bsc-testnet). Default: nile"
    required: false
---

# x402 Payment Demo Skill

This skill demonstrates the x402 payment protocol on the TRON and BSC networks.

## Prerequisites

- The `x402-payment` skill must be installed and usable in the same environment.
- A payment wallet must already be configured for the target network.
- For TRON mainnet, set `TRON_GRID_API_KEY` to avoid rate limits.

## Usage

Simply tell the Agent:
- "demo x402-payment"
- "demo x402-payment on bsc-testnet"
- "demo x402-payment on bsc"

## Network Mapping

- `nile` -> `https://x402-demo.bankofai.io/protected-nile`
- `shasta` -> `https://x402-demo.bankofai.io/protected-shasta`
- `mainnet` -> `https://x402-demo.bankofai.io/protected-mainnet`
- `bsc` -> `https://x402-demo.bankofai.io/protected-bsc-mainnet`
- `bsc-testnet` -> `https://x402-demo.bankofai.io/protected-bsc-testnet`

## Workflow

1.  **Request Resource**: When triggered, follow the instructions provided by the `x402-payment` skill to fetch the protected resource. **Use Tron Nile by default**:
    - **Tron Nile (Default)**: `https://x402-demo.bankofai.io/protected-nile`
    - **Tron Shasta**: `https://x402-demo.bankofai.io/protected-shasta`
    - **Tron Mainnet**: `https://x402-demo.bankofai.io/protected-mainnet`
    - **BSC Mainnet**: `https://x402-demo.bankofai.io/protected-bsc-mainnet`
    - **BSC Testnet**: `https://x402-demo.bankofai.io/protected-bsc-testnet`
2.  **Handle Payment**: Perform the payment and resource acquisition automatically as guided by the protocol (handling 402 Payment Required, signing permits, etc.).
3.  **Display & Cleanup**: Once the image is retrieved, present / send it to the user. Immediately delete the local temporary file after the image has been displayed.

## Notes

- This skill is intended as a demo wrapper around `x402-payment`, not a separate payment implementation.
- If the payment tool returns `file_path`, `content_type`, and `bytes`, the agent should display the file and then remove it immediately.
