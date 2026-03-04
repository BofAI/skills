# SunPerp Perpetual Futures Skill

AI agent skill for trading USDT-margined perpetual futures on [SunPerp](https://www.sunperp.com) (TRON blockchain).

## What This Skill Does

Enables AI agents to interact with SunPerp's REST API to:

- Query real-time market data (prices, order books, candlesticks, funding rates)
- Manage account (balances, fee rates, trading bills)
- Place and cancel orders (market, limit, post-only with TP/SL)
- Manage positions (view, set leverage, set position mode, close)

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Set API Keys

Create keys at https://www.sunperp.com/futures/api-manage/ then:

```bash
export SUNPERP_ACCESS_KEY="your_access_key"
export SUNPERP_SECRET_KEY="your_secret_key"
```

### 3. Test Connection

```bash
# Public endpoint (no auth)
node scripts/market.js ticker contract_code=BTC-USDT

# Authenticated endpoint
node scripts/account.js balance
```

## Scripts

| Script | Purpose |
|---|---|
| `scripts/market.js` | Market data (ticker, depth, kline, funding, etc.) |
| `scripts/account.js` | Account balance, fee rates, bills |
| `scripts/order.js` | Place, cancel, query orders |
| `scripts/position.js` | Positions, leverage, position mode |
| `scripts/wallet.js` | Withdraw USDT, query deposit/withdraw records |
| `scripts/utils.js` | Shared auth/signature utilities |

## Important Disclaimer

This skill covers **trading operations only** (placing orders, managing positions, querying market data). It does **not** handle on-chain wallet operations. The agent operator is responsible for:

- **Deposits**: Manually transferring USDT (TRC-20) to the SunPerp platform
- **Withdrawals**: Manually initiating and confirming withdrawals from SunPerp
- **Private key management**: Never share private keys with agents or store them in skill files

Ensure the trading account is funded before the agent begins trading.

## For AI Agents

Read `SKILL.md` for complete usage instructions, command reference, examples, and error handling guidance.

## License

MIT
