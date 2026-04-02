---
name: x402-payment
description: "Pay for x402-enabled Agent endpoints using ERC20 tokens (USDT/USDC) on EVM or TRC20 tokens (USDT/USDD) on TRON."
version: 1.5.7
author: bankofai
homepage: https://bankofai.io
tags: [crypto, payments, x402, agents, api, usdt, usdd, usdc, tron, ethereum, evm, erc20, trc20]
requires_tools: [x402_invoke]
# Tool implementation mapping: x402_invoke -> src/x402_invoke.ts (run via npx tsx)
arguments:
  url:
    description: "Base URL of the agent (v2) or full URL (v1/Discovery)"
    required: true
  entrypoint:
    description: "Entrypoint name to invoke (e.g., 'chat', 'search')"
    required: false
  input:
    description: "Input object to send to the entrypoint"
    required: false
  method:
    description: "HTTP method (GET/POST). Default: POST (v2), GET (Direct)"
    required: false
  network:
    description: "Network name (nile, mainnet, bsc-testnet, bsc)"
    required: false
dependencies:
  - mcp-server-tron
---

# x402 Payment Skill

Invoke x402-enabled AI agent endpoints with automatic token payments on both TRON (TRC20) and EVM-compatible (ERC20) chains.

## Overview

The `x402-payment` skill enables agents to interact with paid API endpoints. When an agent receives a `402 Payment Required` response, this skill handles the negotiation, signing, and execution of the payment using the `x402_invoke` tool.

## Prerequisites

- **Wallet Configuration (agent-wallet)**:
  - **Local mode (recommended)**: set `AGENT_WALLET_PASSWORD` (required), `AGENT_WALLET_DIR` (optional).
  - **Static mode (env)**: set exactly one of `AGENT_WALLET_PRIVATE_KEY` / `AGENT_WALLET_MNEMONIC`.
  - **Optional for mnemonic mode**: `AGENT_WALLET_MNEMONIC_ACCOUNT_INDEX`.
  - Configure a TRON wallet for TRC20 payments (USDT/USDD) and/or an EVM wallet for ERC20 payments (USDT/USDC).
- **TronGrid API Key (optional)**: `TRON_GRID_API_KEY` is optional. Recommended on **Mainnet** to reduce rate-limit issues.
- **GasFree (optional)**: GasFree credentials are now managed internally by the `@bankofai/x402` library. The tool will prefer the `exact_gasfree` scheme over `exact_permit`. GasFree requires an account that is **activated** with **sufficient token balance** in the GasFree wallet.
- **Dependencies**: Run `npm install` in the `x402-payment/` directory before first use.
- `TRON_GRID_API_KEY` can also be set in `x402-config.json`.

## Usage Instructions

### 1. Verification
Before making payments, verify your wallet status:
```bash
npx tsx x402-payment/src/x402_invoke.ts --check
```

### 2. Invoking an Agent (v2)
Most modern x402 agents use the v2 "invoke" pattern:
```bash
npx tsx x402-payment/src/x402_invoke.ts \
  --url https://api.example.com \
  --entrypoint chat \
  --input '{"prompt": "Your query here"}' \
  --network nile
```

### 3. Agent Discovery (Direct)
- **Manifest**: Fetch agent metadata.
  ```bash
  npx tsx x402-payment/src/x402_invoke.ts --url https://api.example.com/.well-known/agent.json
  ```
- **List Entrypoints**: List available functions.
  ```bash
  npx tsx x402-payment/src/x402_invoke.ts --url https://api.example.com/entrypoints
  ```

### 4. GasFree Wallet Info
Query GasFree wallet information (address, activation status, balance, nonce).
Defaults: network=**mainnet**, wallet=**agent-wallet active TRON wallet**.
```bash
# Default: mainnet + active TRON wallet
npx tsx x402-payment/src/x402_invoke.ts --gasfree-info

# Specify wallet address
npx tsx x402-payment/src/x402_invoke.ts --gasfree-info --wallet <YOUR_WALLET_ADDRESS>

# Specify network
npx tsx x402-payment/src/x402_invoke.ts --gasfree-info --network nile

# Both
npx tsx x402-payment/src/x402_invoke.ts --gasfree-info --wallet <YOUR_WALLET_ADDRESS> --network nile
```
Without `--wallet`, requires a configured TRON wallet from agent-wallet. Returns JSON with `gasFreeAddress`, `active`, `allowSubmit`, `nonce`, and per-token `assets` (balance, fees).

### 5. GasFree Account Activation
Activate a GasFree account that has not been activated yet. Use `--gasfree-info` first to check activation status.
Defaults: network=**nile**, token=**USDT**.
```bash
# Default: nile + USDT
npx tsx x402-payment/src/x402_invoke.ts --gasfree-activate

# Specify network
npx tsx x402-payment/src/x402_invoke.ts --gasfree-activate --network mainnet

# Specify network and token
npx tsx x402-payment/src/x402_invoke.ts --gasfree-activate --network nile --token USDT
```
Requires: TRON wallet configured in agent-wallet. Wallet must have enough tokens to cover activation fees (~3.05 USDT on nile). If the account is already activated, returns `{"status": "already_active"}` immediately.

**Activation process:**
1. Queries GasFree account info and checks activation status
2. Transfers `activateFee + transferFee + 1 token` from wallet to gasFreeAddress (on-chain TRC20)
3. Polls for on-chain confirmation (up to 60s)
4. Submits a GasFree signed transaction to transfer tokens back to wallet (triggers activation)
5. Polls until the GasFree transaction completes

Returns JSON with `status`, `depositTxId`, `gasFreeTraceId`, `gasFreeState`, `gasFreeTxHash`, and final `active` status.

### 6. Cross-Chain Support
- **TRON (TRC20)**: Use `--network nile` (testnet) or `mainnet`.
- **BSC (ERC20)**: Use `--network bsc-testnet` (testnet) or `bsc` (mainnet).

## Supported Networks & Tokens

| Chain | Network Name | Common Tokens | USDT Contract |
|-------|--------------|---------------|---------------|
| **TRON** | `mainnet` | USDT, USDD | `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t` |
| **TRON** | `nile` | USDT, USDD | `TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf` |
| **BSC** | `bsc` | USDT, USDC | `0x55d398326f99059fF775485246999027B3197955` |
| **BSC** | `bsc-testnet`| USDT, USDC, DHLU | `0x337610d27c682E347C9cD60BD4b3b107C9d34dDd` |

## Security Considerations & Rules

> [!CAUTION]
> **Wallet Secret Safety**: NEVER output wallet private keys or mnemonic phrases to logs or console. Use agent-wallet managed configuration.

### Agent Security Rules:
- **No Private Key Output**: The Agent MUST NOT print, echo, or output any private key to the dialogue context.
- **No Mnemonic Output**: The Agent MUST NOT print or expose mnemonic phrases.
- **Internal Loading Only**: Rely on the tool to load wallet credentials internally via agent-wallet.
- **No Export Commands**: DO NOT execute shell commands containing the private key as a literal string.
- **Silent Environment Checks**: Use `[[ -n $AGENT_WALLET_PASSWORD ]] && echo "Configured" || echo "Missing"` to verify local mode configuration without leaking secrets.
- **Use the Check Tool**: Use `npx tsx x402-payment/src/x402_invoke.ts --check` to safely verify addresses.

## Binary and Image Handling

If the endpoint returns an image or binary data:
1. The data is saved to a temporary file (e.g., `/tmp/x402_image_...`).
2. The tool returns JSON with `file_path`, `content_type`, and `bytes`.
3. **Important**: The Agent is responsible for deleting the temporary file after use.

## Error Handling

### Insufficient Allowance
If allowance is insufficient, the tool will automatically attempt an "infinite approval" transaction. Ensure you have native tokens (TRX or BNB/ETH) for gas.

### Insufficient Balance
Ensure you have enough USDT/USDC/USDD in your wallet on the specified network.

### Debug Stack Trace
Set `X402_DEBUG=1` to include full error stack traces in the JSON output when troubleshooting failures.

---
