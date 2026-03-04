---
name: SunPerp Perpetual Futures Trading
description: Trade USDT-margined perpetual futures on SunPerp (TRON) — place orders, manage positions, query market data, and manage account via REST API.
version: 1.0.0
dependencies:
  - node >= 18.0.0
tags:
  - defi
  - perpetual
  - futures
  - tron
  - sunperp
  - trading
author: bankofai
homepage: https://www.sunperp.com
arguments:
  - name: action
    description: The trading action to perform (e.g., market_buy, limit_sell, check_balance, get_price)
    required: true
  - name: contract_code
    description: "Trading pair symbol (e.g., BTC-USDT, ETH-USDT, TRX-USDT)"
    required: false
  - name: volume
    description: Number of contracts to trade
    required: false
  - name: price
    description: Limit price for limit orders
    required: false
  - name: leverage
    description: Leverage multiplier (e.g., 10, 20, 50)
    required: false
---

# SunPerp Perpetual Futures Trading

## Overview

This skill enables AI agents to trade USDT-margined perpetual futures on [SunPerp](https://www.sunperp.com), the perpetual futures DEX on the TRON blockchain. It provides scripts for:

- **Market data**: Prices, order books, candlesticks, funding rates
- **Account management**: Balances, fee rates, trading bills
- **Order management**: Place, cancel, and query orders (market, limit, post-only)
- **Position management**: View positions, set leverage, set position mode, close positions

All scripts communicate with the SunPerp REST API at `https://api.sunx.io`.

## Prerequisites

### 1. Environment Setup

Install Node.js dependencies from the skill directory:

```bash
cd <skill_directory>
npm install
```

### 2. API Key Configuration

The user must create API keys at https://www.sunperp.com/futures/api-manage/ and set them as environment variables:

```bash
export SUNPERP_ACCESS_KEY="your_access_key"
export SUNPERP_SECRET_KEY="your_secret_key"
```

> [!CAUTION]
> Never hardcode API keys in commands or files. Always read them from environment variables. If the environment variables are not set, prompt the user to set them before proceeding.

### 3. Verify Setup

Run a public endpoint to verify connectivity (no API key needed):

```bash
node scripts/market.js ticker contract_code=BTC-USDT
```

Then verify authenticated access:

```bash
node scripts/account.js balance
```

## Usage Instructions

### Contract Code Format

SunPerp contracts follow these naming patterns:

| Type | Format | Example |
|---|---|---|
| Perpetual swap | `{SYMBOL}-USDT` | `BTC-USDT` |
| Current week | `{SYMBOL}-USDT-CW` | `BTC-USDT-CW` |
| Next week | `{SYMBOL}-USDT-NW` | `BTC-USDT-NW` |
| Current quarter | `{SYMBOL}-USDT-CQ` | `BTC-USDT-CQ` |
| Next quarter | `{SYMBOL}-USDT-NQ` | `BTC-USDT-NQ` |

Popular perpetual contracts: `BTC-USDT`, `ETH-USDT`, `TRX-USDT`, `SOL-USDT`, `SUN-USDT`, `DOGE-USDT`, `XRP-USDT`.

### Position Modes

SunPerp supports two position modes:

- **single_side** (One-way): Use `position_side=both` for all orders. The `side` field determines direction.
- **dual_side** (Hedge): Must specify `position_side=long` or `position_side=short`. Allows simultaneous long and short positions.

Check the current mode before trading:

```bash
node scripts/position.js get_mode
```

### Margin Mode

The API uses **cross margin** (`margin_mode=cross`) as the standard mode. All order and position scripts default to cross margin.

---

### Script Reference

All scripts are located in the `scripts/` directory and invoked as:

```bash
node scripts/<script>.js <command> [key=value ...]
```

---

### Market Data (scripts/market.js)

No authentication required for market data.

#### Get 24h Ticker

```bash
node scripts/market.js ticker contract_code=BTC-USDT
```

Returns: open, close, high, low, volume, best bid/ask.

#### Get Order Book

```bash
node scripts/market.js depth contract_code=BTC-USDT type=step0
```

`type` values: `step0` (unmerged, 150 levels) through `step5`; `step6` (unmerged, 20 levels) through `step13`.

#### Get Candlestick Data

```bash
node scripts/market.js kline contract_code=BTC-USDT period=60min size=50
```

`period` values: `1min`, `5min`, `15min`, `30min`, `60min`, `60min`, `4hour`, `1day`, `1mon`.

#### Get Best Bid/Offer

```bash
node scripts/market.js bbo contract_code=BTC-USDT
```

#### Get Last Trade

```bash
node scripts/market.js trade contract_code=BTC-USDT
```

#### Get Recent Trades

```bash
node scripts/market.js trades contract_code=BTC-USDT size=20
```

#### Get Funding Rate

```bash
node scripts/market.js funding contract_code=BTC-USDT
```

#### Get Index Price

```bash
node scripts/market.js index contract_code=BTC-USDT
```

#### List Available Contracts

```bash
node scripts/market.js contracts
```

#### Get Price Limits

```bash
node scripts/market.js price_limit contract_code=BTC-USDT
```

---

### Account (scripts/account.js)

Requires authentication (API keys).

#### Check Account Balance

```bash
node scripts/account.js balance
```

Returns: equity, available margin, unrealized PnL, maintenance margin rate.

#### Get Fee Rates

```bash
node scripts/account.js fee contract_code=BTC-USDT
```

#### Get Trading Bills

```bash
node scripts/account.js bills mar_acct=USDT
```

Optional: `contract=BTC-USDT`, `start_time=<ms>`, `end_time=<ms>`.

---

### Order Management (scripts/order.js)

Requires authentication with **Trade** permission.

#### Place a Market Order

Open a long position (buy):

```bash
node scripts/order.js place contract_code=BTC-USDT side=buy type=market volume=1
```

Open a short position (sell):

```bash
node scripts/order.js place contract_code=BTC-USDT side=sell type=market volume=1
```

#### Place a Limit Order

```bash
node scripts/order.js place contract_code=BTC-USDT side=buy type=limit volume=1 price=95000
```

#### Place an Order with TP/SL

```bash
node scripts/order.js place contract_code=BTC-USDT side=buy type=market volume=1 tp_trigger_price=100000 sl_trigger_price=90000
```

#### Place a Post-Only Order

```bash
node scripts/order.js place contract_code=BTC-USDT side=buy type=post_only volume=1 price=94000
```

#### Place an Order in Hedge Mode

When `position_mode=dual_side`, you must specify `position_side`:

```bash
# Open long
node scripts/order.js place contract_code=BTC-USDT side=buy type=market volume=1 position_side=long

# Close long
node scripts/order.js place contract_code=BTC-USDT side=sell type=market volume=1 position_side=long

# Open short
node scripts/order.js place contract_code=BTC-USDT side=sell type=market volume=1 position_side=short

# Close short
node scripts/order.js place contract_code=BTC-USDT side=buy type=market volume=1 position_side=short
```

#### Cancel an Order

```bash
node scripts/order.js cancel contract_code=BTC-USDT order_id=123456789
```

Or by client order ID:

```bash
node scripts/order.js cancel contract_code=BTC-USDT client_order_id=my_order_1
```

#### Cancel All Orders

```bash
node scripts/order.js cancel_all
```

Optionally filter: `contract_code=BTC-USDT`, `side=buy`, `position_side=long`.

#### Close Position for a Symbol

```bash
node scripts/order.js close contract_code=BTC-USDT position_side=both
```

In hedge mode use `position_side=long` or `position_side=short`.

#### Close All Positions

```bash
node scripts/order.js close_all
```

#### List Open Orders

```bash
node scripts/order.js open_orders contract_code=BTC-USDT
```

#### Get Order Info

```bash
node scripts/order.js info contract_code=BTC-USDT order_id=123456789
```

#### Get Order History

```bash
node scripts/order.js history contract_code=BTC-USDT
```

Optional: `state=filled`, `start_time=<ms>`, `end_time=<ms>`, `limit=50`.

#### Get Execution Details

```bash
node scripts/order.js details contract_code=BTC-USDT order_id=123456789
```

---

### Position Management (scripts/position.js)

Requires authentication.

#### List Open Positions

```bash
node scripts/position.js list
```

Or for a specific contract:

```bash
node scripts/position.js list contract_code=BTC-USDT
```

Returns: entry price, volume, liquidation price, unrealized PnL, margin rate, leverage, ADL risk.

#### Get Current Leverage

```bash
node scripts/position.js get_leverage contract_code=BTC-USDT
```

#### Set Leverage

```bash
node scripts/position.js set_leverage contract_code=BTC-USDT lever_rate=20
```

> [!WARNING]
> Increasing leverage increases liquidation risk. Always confirm the desired leverage with the user before setting it.

#### Get Position Mode

```bash
node scripts/position.js get_mode
```

#### Set Position Mode

```bash
node scripts/position.js set_mode position_mode=single_side
```

> [!NOTE]
> Position mode can only be changed when there are no open positions or orders.

#### Get Risk Limits

```bash
node scripts/position.js risk_limit contract_code=BTC-USDT
```

#### Get Position Limits

```bash
node scripts/position.js position_limit contract_code=BTC-USDT
```

---

### Wallet (scripts/wallet.js)

Requires authentication with **Withdraw** permission. Also requires `TRON_PRIVATE_KEY` env var for signing withdrawal confirmations.

```bash
export TRON_PRIVATE_KEY="your_hex_private_key"
```

#### Withdraw USDT (Full Flow)

Performs the complete two-step withdraw: apply → sign → confirm.

```bash
node scripts/wallet.js withdraw address=TXxxxxxxxxxxxxxxxxxxxxxxxxxxxx amount=10
```

Optional: `currency=usdt` (default), `chain=trc20usdt` (default), `fee=0` (default).

#### Withdraw Apply Only (Step 1)

Returns nonce and content for manual signing:

```bash
node scripts/wallet.js apply address=TXxxxxxxxxxxxxxxxxxxxxxxxxxxxx amount=10
```

#### Withdraw Confirm Only (Step 2)

Confirm a previously applied withdrawal with a pre-computed signature:

```bash
node scripts/wallet.js confirm nonce=<nonce_from_apply> signature=<hex_signature>
```

#### Query Deposit/Withdraw Records

```bash
node scripts/wallet.js records type=deposit
node scripts/wallet.js records type=withdraw
```

Optional: `currency=usdt`, `size=50`, `direct=next`, `from=<id>`.

> [!CAUTION]
> Withdrawals move funds off-platform and are irreversible. Always confirm the destination address and amount with the user before executing.

---

## Examples

### Example 1: Check Price and Open a Long Position

```
User: "Buy 5 contracts of BTC-USDT at market price"

Agent steps:
1. Check the current price:
   node scripts/market.js ticker contract_code=BTC-USDT

2. Check account balance:
   node scripts/account.js balance

3. Confirm with user: "BTC-USDT is currently at $96,500. You have $10,000 available margin.
   Placing a market buy for 5 contracts. Proceed?"

4. After user confirms, place the order:
   node scripts/order.js place contract_code=BTC-USDT side=buy type=market volume=5

5. Verify the position was opened:
   node scripts/position.js list contract_code=BTC-USDT

6. Report: "Opened long position: 5 BTC-USDT contracts at $96,502 avg entry.
   Liquidation price: $48,251. Current unrealized PnL: $0."
```

### Example 2: Set Leverage and Place a Limit Order

```
User: "Set leverage to 20x on ETH-USDT and place a limit buy at $3,200 for 10 contracts"

Agent steps:
1. Set leverage:
   node scripts/position.js set_leverage contract_code=ETH-USDT lever_rate=20

2. Check current price for context:
   node scripts/market.js ticker contract_code=ETH-USDT

3. Confirm with user: "Leverage set to 20x. ETH-USDT is at $3,350.
   Placing limit buy for 10 contracts at $3,200. Proceed?"

4. After user confirms, place the order:
   node scripts/order.js place contract_code=ETH-USDT side=buy type=limit volume=10 price=3200

5. Verify the order was placed:
   node scripts/order.js open_orders contract_code=ETH-USDT

6. Report: "Limit buy order placed: 10 ETH-USDT at $3,200. Order ID: 987654321. Status: open."
```

### Example 3: Close a Position and Check PnL

```
User: "Close my BTC-USDT position"

Agent steps:
1. Check existing position:
   node scripts/position.js list contract_code=BTC-USDT

2. Report position details and confirm:
   "You have a long position of 5 BTC-USDT contracts. Entry: $96,502, Current: $97,100.
   Unrealized PnL: +$2.99. Close at market? Proceed?"

3. After user confirms, close:
   node scripts/order.js close contract_code=BTC-USDT position_side=both

4. Verify:
   node scripts/position.js list contract_code=BTC-USDT

5. Report: "Position closed. Realized PnL: +$2.95 after fees."
```

### Example 4: Monitor Funding Rate

```
User: "What's the funding rate for TRX-USDT?"

Agent steps:
1. Get funding rate:
   node scripts/market.js funding contract_code=TRX-USDT

2. Report: "TRX-USDT funding rate: 0.01% (next funding in 2h 15m).
   Positive rate means longs pay shorts."
```

---

## Error Handling

### Common Error Scenarios

| Error | Cause | Resolution |
|---|---|---|
| Missing env vars | `SUNPERP_ACCESS_KEY` / `SUNPERP_SECRET_KEY` not set | Ask user to set API keys |
| `HTTP 401` | Invalid or expired API keys | Ask user to check/regenerate keys |
| `HTTP 403` | Insufficient permissions | API key needs Trade permission for orders |
| Timestamp error | System clock skew > 5 minutes | Check system time synchronization |
| Insufficient margin | Not enough available margin for the order | Show balance, suggest reducing volume or leverage |
| Position mode conflict | Trying to set mode while positions are open | Close positions first, then switch mode |
| Order rejected | Price outside limits or volume too small | Check `price_limit` and contract info for min/max |

### Error Handling Pattern

When a script returns an error:

1. Parse the error message from the JSON response (`code`, `message`, or `error-msg` fields)
2. Explain the error to the user in plain language
3. Suggest a specific corrective action
4. Do NOT retry automatically for trade operations — always confirm with the user

---

## Security Considerations

> [!CAUTION]
> **Private Keys & API Secrets**: Never log, display, or store API secret keys. Read them exclusively from environment variables.

> [!WARNING]
> **Trade Confirmation**: Always confirm the following with the user BEFORE executing any trade:
> - Contract code and direction (long/short)
> - Order type (market/limit) and volume
> - Price (for limit orders)
> - Current leverage setting
> - Estimated margin requirement

### Security Checklist

- [ ] API keys loaded from environment variables only
- [ ] No secrets in command output or logs
- [ ] Trade confirmations shown before execution
- [ ] Leverage changes confirmed before applying
- [ ] Position mode changes confirmed before applying
- [ ] Close-all operations require explicit user confirmation
- [ ] Cancel-all operations require explicit user confirmation

### User Communication Templates

**Pre-trade confirmation:**
```
📋 Order Summary:
  Contract: {contract_code}
  Side: {side} ({long/short})
  Type: {type}
  Volume: {volume} contracts
  Price: {price or "market"}
  Leverage: {lever_rate}x
  Est. margin: ~${margin}

Proceed? (yes/no)
```

**Post-trade report:**
```
✅ Order executed:
  Order ID: {order_id}
  Avg. fill price: ${trade_avg_price}
  Fee: ${fee}
```

**Position summary:**
```
📊 Position: {contract_code} {direction}
  Volume: {volume} contracts
  Entry: ${open_avg_price}
  Mark: ${mark_price}
  Liq. price: ${liquidation_price}
  Unrealized PnL: ${profit_unreal} ({profit_rate}%)
  Leverage: {lever_rate}x
```

---

*Version 1.0.0 — Created by [M2M Agent Registry](https://m2mregistry.io) for Bank of AI*
