---
name: x402-payment
description: "Pay for x402-enabled Agent endpoints using ERC20 tokens (USDT/USDC) on EVM or TRC20 tokens (USDT/USDD) on TRON."
version: 2.0.0
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

- **Tool**: The `x402_invoke.ts` script in `src/` (run via `npx tsx`).
- **TronGrid API Key**: Required for **Mainnet** to avoid rate limits (`TRON_GRID_API_KEY`).
- **Auto Detection**: The tool automatically detects wallet mode based on environment variables.
- **Dependencies**: Run `npm install` in the `x402-payment/` directory before first use.

### Wallet Configuration

The tool supports **unified agent-wallet** integration with automatic multi-chain support:

#### Option 1: Private Key (Recommended for Development)
Set `AGENT_WALLET_PRIVATE_KEY` with your hex private key (without `0x` prefix):
```bash
export AGENT_WALLET_PRIVATE_KEY="your_private_key_here"
```
This single private key works for **both TRON and EVM chains** automatically.

#### Option 2: Mnemonic Phrase
Set `AGENT_WALLET_MNEMONIC` with your 12/24-word seed phrase:
```bash
export AGENT_WALLET_MNEMONIC="word1 word2 word3 ..."
export AGENT_WALLET_MNEMONIC_ACCOUNT_INDEX="0"  # Optional, defaults to 0
```

#### Option 3: Local Encrypted Wallet
Set `AGENT_WALLET_PASSWORD` to use encrypted local wallets:
```bash
export AGENT_WALLET_PASSWORD="your_password"
export AGENT_WALLET_DIR="~/.agent-wallet"  # Optional, defaults to ~/.agent-wallet
```

### GasFree (Optional)
- **Credentials**: Set `GASFREE_API_KEY` and `GASFREE_API_SECRET` to enable gasless TRC20 payments.
- When configured, the tool will prefer the `exact_gasfree` scheme over `exact_permit`.
- Requires a GasFree account that is **activated** with **sufficient token balance** in the GasFree wallet.
- All keys can also be set in `x402-config.json` or `~/.mcporter/mcporter.json`.

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
Defaults: network=**mainnet**, wallet=**active TRON agent-wallet**.
```bash
# Default: mainnet + active TRON agent-wallet
npx tsx x402-payment/src/x402_invoke.ts --gasfree-info

# Specify wallet address
npx tsx x402-payment/src/x402_invoke.ts --gasfree-info --wallet <YOUR_WALLET_ADDRESS>

# Specify network
npx tsx x402-payment/src/x402_invoke.ts --gasfree-info --network nile

# Both
npx tsx x402-payment/src/x402_invoke.ts --gasfree-info --wallet <YOUR_WALLET_ADDRESS> --network nile
```
Requires: `GASFREE_API_KEY`, `GASFREE_API_SECRET`. Without `--wallet`, requires a configured TRON agent-wallet. Returns JSON with `gasFreeAddress`, `active`, `allowSubmit`, `nonce`, and per-token `assets` (balance, fees).

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
Requires: a configured TRON agent-wallet plus `GASFREE_API_KEY` and `GASFREE_API_SECRET`. Wallet must have enough tokens to cover activation fees (~3.05 USDT on nile). If the account is already activated, returns `{"status": "already_active"}` immediately.

**Activation process:**
1. Queries GasFree account info and checks activation status
2. Builds an unsigned TRC20 transfer with `TronWeb`, signs it with agent-wallet, then broadcasts it on-chain to `gasFreeAddress`
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
> **Private Key Safety**: NEVER output your private keys to the logs or console. The `x402_invoke` tool loads keys from environment variables internally.

### Agent Security Rules:
- **No Private Key Output**: The Agent MUST NOT print, echo, or output any private key to the dialogue context.
- **Internal Loading Only**: Rely on the tool to load keys internally.
- **No Export Commands**: DO NOT execute shell commands containing the private key as a literal string.
- **Silent Environment Checks**: Use `[[ -n $AGENT_WALLET_PRIVATE_KEY ]] && echo "Configured" || echo "Missing"` to verify configuration without leaking secrets.
- **Use the Check Tool**: Use `npx tsx x402-payment/src/x402_invoke.ts --check` to safely verify addresses.
- **Unified Wallet**: The tool only uses agent-wallet and resolves the active wallet from `AGENT_WALLET_PRIVATE_KEY`, `AGENT_WALLET_MNEMONIC`, or `AGENT_WALLET_PASSWORD`.

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

---
*Last Updated: 2026-03-17*
