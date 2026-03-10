---
name: x402-payment
description: "Pay for x402-enabled Agent endpoints using ERC20 tokens (USDT/USDC) on EVM or TRC20 tokens (USDT/USDD) on TRON."
version: 1.5.0
author: bankofai
homepage: https://x402.org
tags: [crypto, payments, x402, agents, api, usdt, usdd, usdc, tron, ethereum, evm, erc20, trc20]
requires_tools: [x402_invoke]
# Tool implementation mapping: x402_invoke -> dist/x402_invoke.js
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

- **Tool**: The `x402_invoke.js` script must be built and available in `dist/`.
- **TronGrid API Key**: Required for **Mainnet** to avoid rate limits (`TRON_GRID_API_KEY`).
- **Auto Detection**: If `AGENT_WALLET_PASSWORD` or `agent_wallet.password` is configured, the tool uses agent wallet mode. Otherwise it falls back to private key mode.

### Mode 1: Private Key
- **TRON**: Set `TRON_PRIVATE_KEY` for TRC20 payments (USDT/USDD).
- **EVM**: Set `EVM_PRIVATE_KEY` or `ETH_PRIVATE_KEY` for ERC20 payments (USDT/USDC).
- The skill also searches for keys in `x402-config.json` and `~/.mcporter/mcporter.json`.

### Mode 2: Agent Wallet
- **Package**: `@bankofai/agent-wallet` must be installed.
- **TRON**: Set `TRON_AGENT_WALLET_NAME` to the agent wallet name for TRON.
- **EVM**: Set `EVM_AGENT_WALLET_NAME` (or `BSC_AGENT_WALLET_NAME`) for EVM.
- **Password**: Set `AGENT_WALLET_PASSWORD` to unlock the wallet.
- **Secrets Dir**: Optionally set `AGENT_WALLET_SECRETS_DIR` (default: `~/.agent-wallet`).
- Alternatively, configure via `x402-config.json` under the `agent_wallet` key.

## Usage Instructions

### 1. Verification
Before making payments, verify your wallet status:
```bash
# Auto-detect wallet mode
node x402-payment/dist/x402_invoke.js --check
```

### 2. Invoking an Agent (v2)
Most modern x402 agents use the v2 "invoke" pattern:
```bash
# Auto-detect wallet mode
node x402-payment/dist/x402_invoke.js \
  --url https://api.example.com \
  --entrypoint chat \
  --input '{"prompt": "Your query here"}' \
  --network nile
```

### 3. Agent Discovery (Direct)
- **Manifest**: Fetch agent metadata.
  ```bash
  node x402-payment/dist/x402_invoke.js --url https://api.example.com/.well-known/agent.json
  ```
- **List Entrypoints**: List available functions.
  ```bash
  node x402-payment/dist/x402_invoke.js --url https://api.example.com/entrypoints
  ```

### 4. Cross-Chain Support
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
> **Private Key Safety**: NEVER output your private keys to the logs or console. The `x402_invoke` tool loads keys from environment variables internally.

### Agent Security Rules:
- **No Private Key Output**: The Agent MUST NOT print, echo, or output any private key to the dialogue context.
- **Internal Loading Only**: Rely on the tool to load keys internally.
- **No Export Commands**: DO NOT execute shell commands containing the private key as a literal string.
- **Silent Environment Checks**: Use `[[ -n $TRON_PRIVATE_KEY ]] && echo "Configured" || echo "Missing"` to verify configuration without leaking secrets.
- **Use the Check Tool**: Use `node x402_invoke.js --check` to safely verify addresses.
- **Agent Wallet Selection**: If `AGENT_WALLET_PASSWORD` is configured, the tool uses agent wallet mode instead of private keys.

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

## Agent Wallet Configuration (x402-config.json)

You can configure agent wallet settings in `x402-config.json` or `~/.x402-config.json`:
```json
{
  "agent_wallet": {
    "tron_wallet_name": "my-tron-wallet",
    "evm_wallet_name": "my-evm-wallet",
    "secrets_dir": "~/.agent-wallet",
    "password": "..."
  }
}
```

> [!WARNING]
> Storing the password in a config file is less secure than using the `AGENT_WALLET_PASSWORD` environment variable.

---
*Last Updated: 2026-03-09*
