# TronScan Data Lookup Skill

AI agent skill for querying TRON blockchain data and read-only security signals via the [TronScan API](https://docs.tronscan.org/).

## Quick Start

```bash
npm install
node scripts/overview.js          # Chain dashboard
node scripts/account.js <address> # Account lookup
node scripts/token.js --price trx # TRX price
node scripts/security.js account <address> # Read-only security check
```

## Scripts

| Script | Purpose |
|--------|---------|
| `search.js` | Universal search (addresses, tokens, contracts, transactions, blocks) |
| `account.js` | Account details, token balances, wallet portfolio, resources |
| `transaction.js` | Transaction lookup by hash, filtered lists, network stats |
| `token.js` | Token info, pricing, holders, supply, rankings |
| `block.js` | Block details, recent blocks, block stats |
| `contract.js` | Smart contract info, energy usage, call analytics |
| `transfer.js` | TRX/TRC10/TRC20 transfer history |
| `overview.js` | Chain overview, TPS, witnesses, governance, market data |
| `security.js` | Account, token, URL, transaction, multi-signature, and approval security signals |

Security checks validate inputs locally and return a normalized assessment plus the complete
TronScan response. `no_known_flags` means only that the current response contains no known flags;
incomplete upstream responses are reported as `unknown`, and neither result guarantees safety.

## Testing

```bash
npm test           # Offline validation and assessment tests
npm run test:live  # Live smoke tests for all configured TronScan endpoints
```

See [SKILL.md](SKILL.md) for full documentation and usage examples.

## License

MIT
