# SunPump Trading Skill

> Buy and sell meme tokens on SunPump, the TRON bonding-curve launchpad.

## Overview

This skill provides AI agents with scripts to trade tokens on [SunPump](https://sunpump.meme) — the leading fair-launch meme token platform on TRON. Tokens are priced via a bonding curve and automatically migrate to SunSwap V2 once they reach ~$69,420 market cap.

## Files

```
sunpump/
├── SKILL.md                          # Full agent instructions
├── README.md                         # This file
├── package.json                      # Node.js dependencies
├── scripts/
│   ├── utils.js                      # Shared utilities
│   ├── balance.js                    # Check TRX & token balances
│   ├── price.js                      # Query price, state, estimates
│   ├── buy.js                        # Purchase tokens with TRX
│   └── sell.js                       # Sell tokens for TRX
├── resources/
│   └── sunpump_contracts.json        # Contract addresses & ABIs
└── examples/
```

## Network

| Network | Launcher Contract | API Endpoint |
|---|---|---|
| Mainnet | `TTfvyrAz86hbZk5iDpKD78pqLGgi8C7AAw` | `https://api.trongrid.io` |
| Nile | `TTfvyrAz86hbZk5iDpKD78pqLGgi8C7AAw` | `https://nile.trongrid.io` |

## Quick Start

```bash
cd sunpump && npm install

export TRON_PRIVATE_KEY="<your-key>"
export TRON_NETWORK="mainnet"

# Check balance
node scripts/balance.js

# Get price
node scripts/price.js <tokenAddress>

# Buy (dry run)
node scripts/buy.js <tokenAddress> 100 --dry-run

# Sell
node scripts/sell.js <tokenAddress> all
```

## Dependencies

- Node.js 18+
- [tronweb](https://www.npmjs.com/package/tronweb)
