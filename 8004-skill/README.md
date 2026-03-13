# ERC-8004: Trustless Agents on TRON & BSC

On-chain identity, reputation, and validation for autonomous agents on TRON and BSC.

**Now live on TRON Mainnet + BSC Mainnet! Multi-chain support: TRON ✅ | BSC ✅**

## What is ERC-8004?

ERC-8004 is a multi-chain protocol for trustless AI agents, extending the Agent-to-Agent (A2A) Protocol with a trust layer. TRON implementation is called TRC-8004.

The protocol provides three lightweight on-chain registries:

| Registry | Purpose | Details |
|----------|---------|---------|
| **Identity** | Agent discovery & portable identifiers | TRC-721 with URIStorage |
| **Reputation** | Feedback & attestation system | Signed fixed-point scores |
| **Validation** | Independent verification hooks | TEE, zkML, staking |

## Contract Addresses

### TRON Mainnet
- **Identity Registry:** [`TFLvivMdKsk6v2GrwyD2apEr9dU1w7p7Fy`](https://tronscan.org/#/contract/TFLvivMdKsk6v2GrwyD2apEr9dU1w7p7Fy)
- **Reputation Registry:** [`TFbvfLDa4eFqNR5vy24nTrhgZ74HmQ6yat`](https://tronscan.org/#/contract/TFbvfLDa4eFqNR5vy24nTrhgZ74HmQ6yat)
- **Validation Registry:** [`TLCWcW8Qmo7QMNoAKfBhGYfGpHkw1krUEm`](https://tronscan.org/#/contract/TLCWcW8Qmo7QMNoAKfBhGYfGpHkw1krUEm)

### Nile Testnet
- **Identity Registry:** [`TDDk4vc69nzBCbsY4kfu7gw2jmvbinirj5`](https://nile.tronscan.org/#/contract/TDDk4vc69nzBCbsY4kfu7gw2jmvbinirj5)
- **Reputation Registry:** [`TBVaGd6mBuGuN5ebcvPvRaJo4rtEWqsW6Y`](https://nile.tronscan.org/#/contract/TBVaGd6mBuGuN5ebcvPvRaJo4rtEWqsW6Y)
- **Validation Registry:** [`TGGkHDHhBzhFcLNcEogAWJkvfFYy4jyrSw`](https://nile.tronscan.org/#/contract/TGGkHDHhBzhFcLNcEogAWJkvfFYy4jyrSw)

### Shasta Testnet
- **Identity Registry:** [`TH775ZzfJ5V25EZkFuX6SkbAP53ykXTcma`](https://shasta.tronscan.org/#/contract/TH775ZzfJ5V25EZkFuX6SkbAP53ykXTcma)
- **Reputation Registry:** [`TTkds2ZZKBTChZHho4wcWAa7eWQTxh5TUT`](https://shasta.tronscan.org/#/contract/TTkds2ZZKBTChZHho4wcWAa7eWQTxh5TUT)
- **Validation Registry:** [`TQBFHtKRiaQjc1xp4LtmmXKYdA7JLN89w3`](https://shasta.tronscan.org/#/contract/TQBFHtKRiaQjc1xp4LtmmXKYdA7JLN89w3)

## Multi-Chain Support

ERC-8004 now supports multiple blockchains! Register and manage agents across:

- ✅ **TRON** (Mainnet, Nile, Shasta) - Fully operational
- ✅ **BSC** (BNB Smart Chain) - Live on mainnet and testnet!

### BSC Contract Addresses

**BSC Mainnet:**
- Identity Registry: [`0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`](https://bscscan.com/address/0x8004A169FB4a3325136EB29fA0ceB6D2e539a432)
- Reputation Registry: [`0x8004BAa17C55a88189AE136b182e5fdA19dE9b63`](https://bscscan.com/address/0x8004BAa17C55a88189AE136b182e5fdA19dE9b63)
- Validation Registry: [`0x8004Cc8439f36fd5F9F049D9fF86523Df6dAAB58`](https://bscscan.com/address/0x8004Cc8439f36fd5F9F049D9fF86523Df6dAAB58)

**BSC Testnet:**
- Identity Registry: [`0x8004A818BFB912233c491871b3d84c89A494BD9e`](https://testnet.bscscan.com/address/0x8004A818BFB912233c491871b3d84c89A494BD9e)
- Reputation Registry: [`0x8004B663056A597Dffe9eCcC1965A193B7388713`](https://testnet.bscscan.com/address/0x8004B663056A597Dffe9eCcC1965A193B7388713)
- Validation Registry: [`0x8004Cb1BF31DAf7788923b405b754f57acEB4272`](https://testnet.bscscan.com/address/0x8004Cb1BF31DAf7788923b405b754f57acEB4272)

**Note:** BSC deployments use full ERC-8004 specification with all standard methods.

### Chain Compatibility Notes

**TRON (TRC-8004):** Contract versions may vary across networks. Query scripts use compatibility mode:
- ✅ Always available: `ownerOf`, `tokenURI` (ERC-721 standard)
- ⚠️ May vary by deployment: `agentURI`, `getAgentWallet`, `agentExists` (ERC-8004 extensions)

**BSC:** Full ERC-8004 specification support on all networks.

Use `--chain` parameter to specify the blockchain:

```bash
# Register on TRON
node scripts/register.js --uri "ipfs://..." --chain tron --network mainnet

# Register on BSC
node scripts/register.js --uri "ipfs://..." --chain bsc --network mainnet

# Register on BSC testnet
node scripts/register.js --uri "ipfs://..." --chain bsc --network testnet
```

## Quick Start

### Prerequisites

```bash
# Install Node.js and npm
# https://nodejs.org/

# Install dependencies (from the repository `skills/8004-skill` directory)
npm install

# Configure private key (works for both TRON and BSC):

# Method 1: Environment variable (recommended)
export TRON_PRIVATE_KEY="your_64_character_hex_private_key"

# Method 2: File storage
mkdir -p ~/.clawdbot/wallets
echo "your_private_key" > ~/.clawdbot/wallets/.deployer_pk
chmod 600 ~/.clawdbot/wallets/.deployer_pk
```

### Register an Agent

```bash
# TRON Mainnet
node scripts/register.js --uri "ipfs://QmYourHash..." --chain tron --network mainnet

# TRON Testnet (Nile)
node scripts/register.js --uri "ipfs://QmYourHash..." --chain tron --network nile

# BSC Mainnet
node scripts/register.js --uri "ipfs://QmYourHash..." --chain bsc --network mainnet

# BSC Testnet
node scripts/register.js --uri "ipfs://QmYourHash..." --chain bsc --network testnet

# Register without URI (set later)
node scripts/register.js --chain tron --network nile
```

### Query Agent Information

```bash
# Query agent details
node scripts/query.js agent 1 --chain tron --network nile

# Query reputation summary
node scripts/query.js reputation 1 --chain bsc --network testnet
```

### Search Agents (via search-service)

```bash
# Search on TN search-service
node scripts/search.js --query "ainft" --url "https://tn-search-service.bankofai.io" --chain-id 3448148188

# Search only BSC mainnet
node scripts/search.js --query "a2a x402" --chain-id 56

# Search multiple chains
node scripts/search.js --query "payment agent" --chains "56,3448148188"

# Search all chains configured in search-service
node scripts/search.js --query "merchant recharge" --chains all

# Filter only active x402 agents
node scripts/search.js --query "payment" --active true --x402 true
```

### Submit Feedback

```bash
# Quality score 95/100
node scripts/feedback.js --agent-id 1 --score 95 --tag1 "quality" --chain tron --network nile

# Uptime percentage 99.77%
node scripts/feedback.js --agent-id 1 --score 9977 --decimals 2 --tag1 "uptime" --chain bsc --network testnet
```

### Update Agent URI

```bash
# Update metadata URI (owner only)
node scripts/set-uri.js --agent-id 1 --uri "ipfs://QmNewHash" --chain tron --network mainnet
```

## Agent Registration Format

Your `agentURI` should resolve to a JSON registration file:

```json
{
  "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
  "name": "My Agent",
  "description": "An autonomous agent that...",
  "image": "ipfs://QmImageHash...",
  "services": [
    { "name": "A2A", "endpoint": "https://agent.example/.well-known/agent-card.json" },
    { "name": "MCP", "endpoint": "https://mcp.agent.example/" }
  ],
  "registrations": [
    { "agentRegistry": "tron:728126428:TFLvivMdKsk6v2GrwyD2apEr9dU1w7p7Fy", "agentId": "1" }
  ],
  "supportedTrust": ["reputation"]
}
```

See `templates/registration.json` for a complete example.

## Trust Models

ERC-8004 supports pluggable trust mechanisms:

- **Reputation-based** - Client feedback with scores (0-100), tags, and off-chain metadata
- **Crypto-economic** - Stake-secured validation with economic incentives  
- **Crypto-verification** - TEE attestations and zkML proofs for cryptographic trust

## Reputation Scores

The reputation system uses signed fixed-point numbers (`value` + `valueDecimals`):

| Tag | Meaning | Example | value | decimals |
|-----|---------|---------|-------|----------|
| quality | Quality (0-100) | 87/100 | 87 | 0 |
| uptime | Uptime % | 99.77% | 9977 | 2 |
| yield | Yield % | -3.2% | -32 | 1 |
| latency | Latency ms | 560ms | 560 | 0 |

## Network Configuration

All network configurations and contract addresses are stored in `lib/contracts.json`.

Supported networks:
- **mainnet** - TRON Mainnet (production)
- **nile** - Nile Testnet (recommended for testing)
- **shasta** - Shasta Testnet (alternative testnet)

## Private Key Configuration

ERC-8004 supports multiple methods for private key configuration:

**Priority Order:**
1. `TRON_PRIVATE_KEY` environment variable
2. `PRIVATE_KEY` environment variable
3. `~/.clawdbot/wallets/.deployer_pk` file

**Setup Examples:**

```bash
# Method 1: Environment variable (temporary)
export TRON_PRIVATE_KEY="your_private_key"

# Method 2: Environment variable (persistent)
echo 'export TRON_PRIVATE_KEY="your_key"' >> ~/.bashrc
source ~/.bashrc

# Method 3: File storage (shared with ERC-8004)
mkdir -p ~/.clawdbot/wallets
echo "your_private_key" > ~/.clawdbot/wallets/.deployer_pk
chmod 600 ~/.clawdbot/wallets/.deployer_pk
```

## Resources

### Official
- 🌐 [EIP-8004 Specification](https://eips.ethereum.org/EIPS/eip-8004) - Full specification
- 🏠 [8004.org](https://8004.org) - Official website
- 💬 [Telegram Community](https://t.me/ERC8004) - Builder chat
- 🚀 [Builder Program](http://bit.ly/8004builderprogram) - Join the ecosystem

### TRON Resources
- 📚 [TRON Documentation](https://developers.tron.network/)
- 🔍 [TronScan](https://tronscan.org/) - Block explorer
- 🛠️ [TronWeb](https://github.com/tronprotocol/tronweb) - JavaScript SDK

### Related
- 🤝 [A2A Protocol](https://a2a-protocol.org/) - Agent-to-Agent protocol that TRC-8004 extends
- 📖 [Awesome ERC-8004](https://github.com/sudeepb02/awesome-erc8004) - Curated resource list

## Differences from Ethereum ERC-8004

TRON implementation (TRC-8004) maintains full compatibility with ERC-8004 while adapting to TRON's ecosystem:

- Uses TRON addresses (Base58 format starting with 'T')
- Energy/Bandwidth instead of gas fees
- TRC-721 instead of ERC-721 for identity tokens
- Network identifiers use TRON chain ID (728126428 for mainnet)

## License

CC0 - Public Domain

---

*Part of the BofAI Skills repository*
