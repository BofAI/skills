---
name: TronScan Data Lookup
description: Query TRON blockchain data and read-only security signals via the TronScan API — accounts, transactions, tokens, blocks, contracts, transfers, chain statistics, permissions, approvals, and phishing indicators.
version: 1.0.0
dependencies:
  - axios
tags:
  - blockchain
  - tron
  - tronscan
  - api
  - data
  - account
  - transaction
  - token
  - block
  - contract
  - transfer
  - analytics
  - security
---

# TronScan Data Lookup Skill

## Overview

This skill enables AI agents to query the TRON blockchain through the TronScan API. It provides nine Node.js scripts that cover universal search, account details, transactions, token info, blocks, smart contracts, transfer history, chain-level statistics, and read-only security checks.

All scripts output structured JSON to stdout and log progress to stderr, following the bankofai skill conventions.

## Prerequisites

- **Node.js** >= 16
- **npm** (for installing dependencies)
- Run `npm install` in the skill root directory before first use

### API Key (Optional)

If no API key is configured, scripts automatically use the **BofAI proxy** (`ts.bankofai.io`) — no setup needed.

To use your own TronScan API key instead (higher rate limits), set the environment variable:

```bash
export TRONSCAN_API_KEY="your-api-key-here"
```

Get a free key at https://tronscan.org/#/myaccount/apiKeys

### Rate Limits

- **Maximum 5 requests per second**
- **Maximum 100,000 total requests** on the free-tier key
- All endpoints use HTTP GET (except contract event batch queries)
- Maximum `limit` per request is 200 (some endpoints allow up to 500)
- `start + limit` must be <= 10,000 for paginated endpoints

## Usage Instructions

### 1. Universal Search

Search across addresses, tokens, contracts, transactions, and blocks.

```bash
node scripts/search.js <term> [--type <type>] [--limit <n>]
```

**Parameters:**
| Param | Description | Values |
|-------|-------------|--------|
| `term` | Search query (positional, required) | Any string |
| `--type` | Filter result type | `token`, `address`, `contract`, `transaction`, `block` |
| `--limit` | Max results | 1–50, default 20 |

**When to use:** When you have a partial name, address, hash, or need to identify what something is on TRON.

---

### 2. Account Details

Look up account information, balances, token holdings, and resource usage.

```bash
node scripts/account.js <address>                          # Full account details
node scripts/account.js <address> --tokens [--limit <n>]   # Token holdings
node scripts/account.js <address> --wallet                 # Portfolio with USD values
node scripts/account.js <address> --resources              # Bandwidth & energy
node scripts/account.js <address> --analysis --type <0-4>  # Daily analytics
```

**Modes:**
| Flag | Description |
|------|-------------|
| *(none)* | Full account detail (balance, creation date, permissions, witness status) |
| `--tokens` | All token balances. Use `--show 1` for TRC20 only, `2` for TRC721, `3` for all, `4` for TRC1155 |
| `--wallet` | Portfolio view with USD-denominated values |
| `--resources` | Bandwidth/energy allocation (Stake 2.0) |
| `--analysis` | Daily analytics. `--type`: 0=balance, 1=transfers, 2=energy, 3=bandwidth, 4=transactions |

**When to use:** When a user asks about a TRON wallet's balance, token holdings, staking resources, or account history.

---

### 3. Transaction Lookup

Retrieve individual transactions by hash or list transactions with filters.

```bash
node scripts/transaction.js <hash>                                  # By hash
node scripts/transaction.js --list [--from <addr>] [--to <addr>]    # Filtered list
node scripts/transaction.js --stats                                 # Network stats
```

**List options:**
| Param | Description |
|-------|-------------|
| `--from` | Filter by sender address |
| `--to` | Filter by receiver address |
| `--block` | Filter by block number |
| `--start_timestamp` | Start time (ms) |
| `--end_timestamp` | End time (ms) |
| `--sort` | Sort field (default: `-timestamp`) |
| `--limit` | Results per page (default 20, max 200) |
| `--start` | Pagination offset |

**When to use:** When a user wants to look up a specific transaction hash, or query recent transactions for an address.

---

### 4. Token Information

Get token details, pricing, holder lists, supply data, and rankings.

```bash
node scripts/token.js --list [--filter <type>] [--sort <field>]   # Token rankings
node scripts/token.js --trc20 <contract_address>                  # TRC20 detail
node scripts/token.js --trc10 <token_id>                          # TRC10 detail
node scripts/token.js --price [symbol]                            # Current price
node scripts/token.js --holders <contract_address> [--limit <n>]  # Top holders
node scripts/token.js --supply <contract_address>                 # Total supply
node scripts/token.js --distribution <token_id>                   # Holdings distribution
```

**List filters:** `trc10`, `trc20`, `trc721`, `trc1155`, `all`, `top`
**Sort fields:** `priceInTrx`, `gain`, `volume24hInTrx`, `holderCount`, `marketcap`

**When to use:** When a user asks about a specific token (price, holders, supply), or wants to browse top tokens on TRON.

---

### 5. Block Information

Query block details, recent blocks, or block statistics.

```bash
node scripts/block.js                                     # Latest block
node scripts/block.js <number>                            # By block number
node scripts/block.js --list --limit <n>                  # Recent blocks
node scripts/block.js --producer <address>                # By block producer
node scripts/block.js --stats                             # Network block stats
```

**When to use:** When a user wants to see the latest block, look up a specific block, or view block production statistics.

---

### 6. Smart Contract Details

Look up contract info, energy usage, call statistics, and caller analytics.

```bash
node scripts/contract.js <address>                         # Contract detail
node scripts/contract.js --list [--search <term>]          # Search/list contracts
node scripts/contract.js <address> --energy                # Energy consumption
node scripts/contract.js <address> --calls                 # Call statistics
node scripts/contract.js <address> --callers               # Caller list
node scripts/contract.js <address> --analysis --type <0-5> # Daily analytics
```

**Analysis types:** 0=callers, 1=calls, 2=energy, 3=bandwidth, 4=trx_transfers, 5=token_transfers

**When to use:** When a user asks about a smart contract's code verification status, usage, energy costs, or who is calling it.

---

### 7. Transfer History

Query TRX, TRC10, and TRC20 transfer history for addresses and contracts.

```bash
node scripts/transfer.js --trx <address>                             # TRX transfers
node scripts/transfer.js --trc20 <address> --token <contract>        # TRC20 transfers
node scripts/transfer.js --trc10 <address> --token <token_id>        # TRC10 transfers
node scripts/transfer.js --trc20-contract <contract> [--addr <addr>] # By contract
node scripts/transfer.js --internal <address>                        # Internal txns
```

**Common options:**
| Param | Description |
|-------|-------------|
| `--token` | Required contract address for `--trc20`, or token ID for `--trc10` |
| `--direction` | `0`=all, `1`=incoming, `2`=outgoing |
| `--start_timestamp` | Start time (ms) |
| `--end_timestamp` | End time (ms) |
| `--limit` | Results per page (default 20, max 200) |

**When to use:** When a user wants to see transfer history for a wallet — incoming/outgoing TRX, USDT, or other tokens.

---

### 8. Chain Overview & Statistics

Get high-level TRON network data, super representatives, governance, and market data.

```bash
node scripts/overview.js                         # Full chain dashboard
node scripts/overview.js --tps                   # Current transactions per second
node scripts/overview.js --witnesses              # Super Representative list
node scripts/overview.js --params                 # Chain parameters
node scripts/overview.js --proposals              # Governance proposals
node scripts/overview.js --daily-accounts [days]  # New account growth
node scripts/overview.js --funds                  # TRX supply & burn data
node scripts/overview.js --trx-volume             # TRX price/volume history
node scripts/overview.js --nodes                  # Network node map
```

**When to use:** When a user asks about TRON network health, TPS, super representatives, governance, TRX supply, or market data.

---

### 9. Security Checks

Query TronScan security signals without signing or broadcasting a transaction:

```bash
node scripts/security.js account <address>
node scripts/security.js token <token-id-or-contract>
node scripts/security.js url <public-url>
node scripts/security.js transaction <hash> [hash ...]
node scripts/security.js multisig <address>
node scripts/security.js approvals <address>
```

| Mode | Checks |
|------|--------|
| `account` | Fraud history, spam memos, fraudulent token creation, stablecoin blacklist signal |
| `token` | Token level, blacklist/supply capabilities, URL-like names, source visibility, proxy use |
| `url` | TronScan phishing, scam, or malicious-link signal |
| `transaction` | Risky tokens/addresses, zero-value transfers, same-tail impersonation, overall risk |
| `multisig` | Owner/active permission structure and locally derived threshold observations |
| `approvals` | Risky token approvals and unlimited risky allowances |

Endpoint paths are defined in `resources/api_config.json`.

The script validates Base58Check addresses and 64-character transaction hashes before querying.
This is required because several TronScan security endpoints return default `false` values or omit
invalid inputs instead of reporting an error. URL query parameters and fragments are removed before
transmission so credentials or private query values are not sent to the API.

Output is a JSON object with:

- `query`: normalized mode and subject;
- `assessment.status`: `no_known_flags`, `review_required`, or `unknown`;
- `assessment.signals`: fields requiring review;
- `assessment.unknownReasons`: missing or incomplete upstream security fields, when applicable;
- `assessment.unresolved`: transaction hashes omitted by the upstream API, when applicable;
- `data`: the complete TronScan response.

Treat `no_known_flags` as a narrow statement about the current TronScan response, never as proof
that an account, token, URL, transaction, permission structure, or approval is safe. Corroborate
material decisions with contract source, transaction details, and another current source.

**When to use:** Before interacting with an unfamiliar TRON address, token, DApp URL, transaction,
multi-signature account, or existing token approval.

## Examples

### Look up a TRON wallet and its USDT balance

```bash
# Get full account info
node scripts/account.js TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf

# Get token holdings with USD values
node scripts/account.js TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf --wallet
```

### Check a transaction

```bash
node scripts/transaction.js 7f4a6d28e3c5f1b2a9d8e7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6
```

### Get the current TRX price

```bash
node scripts/token.js --price trx
```

### List top 10 TRC20 tokens by market cap

```bash
node scripts/token.js --list --filter trc20 --sort marketcap --limit 10
```

### Get recent USDT transfers for an address

```bash
node scripts/transfer.js --trc20 TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf --token TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t --limit 10
```

### Get chain overview

```bash
node scripts/overview.js
```

### Check a token and an account before interacting

```bash
node scripts/security.js token TPYmHEhy5n8TCEfYGqW2rPxsghSfzghPDn
node scripts/security.js account TT2T17KZhoDu47i2E4FWxfG79zdkEWkU9N
```

Representative account-check output:

```json
{
  "query": {
    "mode": "account",
    "subject": "TT2T17KZhoDu47i2E4FWxfG79zdkEWkU9N"
  },
  "assessment": {
    "status": "no_known_flags",
    "signals": [],
    "caveat": "TronScan signals are one data source, not proof that a target is safe."
  },
  "data": {
    "send_ad_by_memo": false,
    "has_fraud_transaction": false,
    "fraud_token_creator": false,
    "is_black_list": false
  }
}
```

### Review approvals and multi-signature permissions

```bash
node scripts/security.js approvals THSiB9MT2sCnAUgnYs9euMCY9aiZCD4HB5
node scripts/security.js multisig THSiB9MT2sCnAUgnYs9euMCY9aiZCD4HB5
```

## Error Handling

All scripts handle errors consistently:

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing required argument` | Required positional arg not provided | Check usage in script header |
| `Request failed with status 403` | API key invalid or rate limited | Check `TRONSCAN_API_KEY`, reduce request frequency |
| `Request failed with status 404` | Endpoint not found or invalid params | Verify address/hash format |
| `timeout of 15000ms exceeded` | API server slow or unreachable | Retry after a few seconds |
| `ENOTFOUND` | No network connectivity | Check internet connection |
| `Invalid TRON address` | Bad prefix, alphabet, length, or checksum | Re-copy the Base58Check address from a trusted source |
| `assessment.status: unknown` | A transaction hash was omitted or expected security fields were missing upstream | Verify the target exists, then retry or use the corresponding lookup script |

Scripts exit with code 1 on error and output `{ "error": "message" }` to stdout for machine parsing.

## Security Considerations

- The API key is **read-only** — it cannot modify blockchain state
- The API key is loaded exclusively from the `TRONSCAN_API_KEY` environment variable and is never hardcoded
- When no API key is set, requests go through the BofAI proxy (`ts.bankofai.io`) with no key header
- Never embed private keys or wallet secrets in script invocations
- All queries are **read-only GET requests** against the public TronScan API
- Security checks send only public addresses, token IDs, transaction hashes, or a sanitized public URL
- URL credentials are rejected; query parameters and fragments are stripped before transmission
- Do not submit private/internal URLs or paths containing secrets; path components are not removed
- A clear security response is not a guarantee of safety and must not override contradictory evidence
- The API key should be rotated if ever exposed in logs or public repositories
- Rate limit to **5 requests/second** maximum to avoid key revocation

## Common Token Addresses

The `resources/common_tokens.json` file contains well-known mainnet token addresses. Key tokens:

| Symbol | Contract Address | Decimals |
|--------|-----------------|----------|
| TRX | *(native)* | 6 |
| USDT | TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t | 6 |
| USDC | TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8 | 6 |
| USDD | TPYmHEhy5n8TCEfYGqW2rPxsghSfzghPDn | 18 |
| WTRX | TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR | 6 |
| BTT | TAFjULxiVgT4qWk6UZwjqwZXTSaGaqnVp4 | 18 |
| JST | TCFLL5dx5ZJdKnWuesXxi1VPwjLVmWZZy9 | 18 |
| SUN | TSSMHYeV2uE9qYH95DqyoCuNCzEL1NvU3S | 18 |

Agents can use these addresses directly instead of searching for them.

---

*Version 1.0.0 — Created by [M2M Agent Registry](https://m2mregistry.io) for Bank of AI*
