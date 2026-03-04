# Multi-Sig & Account Permissions

🔐 Configure TRON's native account permission system and coordinate multi-signature transactions.

## Quick Start

```bash
cd multisig-permissions && npm install
export TRON_PRIVATE_KEY="<your-key>"
export TRON_NETWORK="mainnet"

# Check current permissions
node scripts/status.js

# Set up 2-of-3 multi-sig
node scripts/update.js from-template basic-2of3 \
  --key1 TKey1... --key2 TKey2... --key3 TKey3... --dry-run

# Multi-sig transaction flow
node scripts/propose.js transfer TRecipient... 10000 --memo "Payment"
node scripts/approve.js prop_xxxxx_xxxx
node scripts/execute.js prop_xxxxx_xxxx
```

## Scripts

- **status.js** — View account permission configuration and security analysis
- **update.js** — Modify permissions (add/remove keys, set thresholds, scope operations, apply templates)
- **propose.js** — Create multi-sig transaction proposals (TRX transfer, TRC20 transfer, contract call)
- **approve.js** — Add your signature to a pending proposal
- **execute.js** — Broadcast a fully-signed transaction to the network
- **pending.js** — List and filter pending multi-sig proposals

## Templates

| Template | Description |
|----------|-------------|
| `basic-2of3` | Standard 2-of-3 multi-sig |
| `agent-restricted` | Agent limited to smart contract calls only |
| `team-tiered` | 3-of-5 owner, 2-of-3 active for daily ops |
| `weighted-authority` | Primary key has extra weight |

## Dependencies

- Node.js >= 18.0.0
- tronweb ^6.0.0

## Version

1.0.0 (March 2026)

## License

MIT — see LICENSE for details.
