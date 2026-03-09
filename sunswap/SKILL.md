---
name: SunSwap DEX Trading
description: Execute token swaps on SunSwap DEX for TRON blockchain using automated scripts.
version: 2.0.0
dependencies:
  - node >= 18.0.0
  - tronweb
tags:
  - defi
  - dex
  - swap
  - tron
  - sunswap
---

# SunSwap DEX Trading Skill

## 🚀 Quick Start

This skill provides automated scripts for token swaps on SunSwap DEX. No complex MCP calls needed!

### Prerequisites

1. **Install dependencies** (first time only):
   ```bash
   cd ~/.openclaw/skills/sunswap
   npm install
   ```

2. **Set environment variables**:
   ```bash
   export TRON_PRIVATE_KEY="your_private_key_here"
   export TRONGRID_API_KEY="your_api_key_here"  # Optional, for mainnet
   ```

---

## 📋 Available Scripts

### 1. Check Balance
```bash
node scripts/balance.js [TOKEN_SYMBOL_OR_ADDRESS] [--network nile|mainnet]
```

**Parameters:**
- `TOKEN_SYMBOL_OR_ADDRESS`: Token symbol (e.g., USDT, TRX) or contract address (e.g., TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf)

**Examples:**
```bash
# Check all token balances
node scripts/balance.js

# Check specific token by symbol
node scripts/balance.js TRX
node scripts/balance.js USDT --network mainnet

# Check specific token by address
node scripts/balance.js TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf
```

**Output:** JSON with wallet address and token balances

---

### 2. Get Token USD Price
```bash
node scripts/price.js <TOKEN_SYMBOL_OR_ADDRESS> [--network nile|mainnet]
```

This script calls the public price API from Sun (`https://open.sun.io/apiv2/price`) using the token address.

**Parameters:**
- `TOKEN_SYMBOL_OR_ADDRESS`: Token symbol (e.g., TRX, USDT) or contract address (e.g., T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb)
- `--network`: Network to use for symbol resolution (`nile` or `mainnet`, default: `nile`).  
  This only affects how symbols are mapped to addresses using `resources/common_tokens.json`.  
  The price API itself is address-based.

**Examples:**
```bash
# Get TRX price on Nile (symbol → address via common_tokens.json)
node scripts/price.js TRX

# Get TRX price on mainnet (symbol resolution uses mainnet section)
node scripts/price.js TRX --network mainnet

# Get price by explicit token address
node scripts/price.js T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb
```

**Output:** JSON to stdout with fields:
- `token` - Input token symbol or address
- `tokenAddress` - Resolved token address
- `network` - Network used for symbol resolution
- `priceUSD` - Latest price in USD
- `lastUpdated` - Milliseconds timestamp from API
- `source` - Price API endpoint (`https://open.sun.io/apiv2/price`)

Example JSON:
```json
{
  "token": "TRX",
  "tokenAddress": "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",
  "network": "nile",
  "priceUSD": 0.281424962354,
  "lastUpdated": 1771928248488,
  "source": "https://open.sun.io/apiv2/price"
}
```

The script also prints a human-readable summary to stderr for logging.

---

### 3. Get Price Quote
```bash
node scripts/quote.js <FROM_TOKEN> <TO_TOKEN> <AMOUNT> [--network nile|mainnet]
```

**Parameters:**
- `FROM_TOKEN`: Source token symbol (e.g., USDT, TRX) or contract address (e.g., TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf)
- `TO_TOKEN`: Destination token symbol or contract address
- `AMOUNT`: Amount to swap (in token units)

**Examples:**
```bash
# Get quote using token symbols
node scripts/quote.js TRX USDT 100

# Get quote using contract addresses
node scripts/quote.js TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf TYsbWxNnyTgsZaTFaue9hqpxkU3Fkco94a 0.1

# Mix symbols and addresses
node scripts/quote.js USDT TYsbWxNnyTgsZaTFaue9hqpxkU3Fkco94a 50

# Get quote on mainnet
node scripts/quote.js USDT TRX 50 --network mainnet
```

**Output:** JSON with price, route, and price impact

---

### 3. Get Token Spot Price (Sun Open API)

```bash
node scripts/price.js <TOKEN_SYMBOL_OR_ADDRESS> [--currency USD]
```

**Parameters:**
- `TOKEN_SYMBOL_OR_ADDRESS`: Token symbol on **mainnet** (e.g., TRX, USDT) or contract address
- `--currency`: Fiat currency code (default: `USD`)

**Examples:**
```bash
# TRX price by symbol (mainnet)
node scripts/price.js TRX

# TRX price by contract address (mainnet)
node scripts/price.js T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb

# USDT price with explicit currency
node scripts/price.js USDT --currency USD
```

**Output (stdout JSON):**
- `tokenSymbol` - Token symbol (if known)
- `tokenAddress` - Token TRC20 address
- `currency` - Fiat currency (e.g., USD)
- `price` - Parsed numeric price
- `priceRaw` - Raw string price from API
- `lastUpdated` - Raw timestamp from API
- `lastUpdatedISO` - Parsed ISO timestamp (if provided)

**Notes:**
- This script uses **Sun Open API** endpoint `https://open.sun.io/apiv2/price?tokenAddress=...`  
- Only **mainnet** token prices are supported (symbol resolution uses `mainnet` section of `resources/common_tokens.json`)

---

### 4. Execute Swap (Flexible Workflow)
```bash
node scripts/swap.js <FROM_TOKEN> <TO_TOKEN> <AMOUNT> [OPTIONS]
```

**Parameters:**
- `FROM_TOKEN`: Source token symbol or contract address
- `TO_TOKEN`: Destination token symbol or contract address
- `AMOUNT`: Amount to swap

**Options:**
- `--network <nile|mainnet>` - Network to use (default: nile)
- `--slippage <0.5>` - Slippage tolerance in % (default: 0.5)
- `--recipient <address>` - Recipient address (default: your wallet)
- `--execute` - Execute the swap (without this, dry-run only)
- `--check-only` - Only check balance and allowance
- `--approve-only` - Only approve token (if needed)
- `--swap-only` - Only execute swap (assumes already approved)

**Examples:**

```bash
# 🔍 Dry run using symbols (check everything, show what would happen)
node scripts/swap.js TRX USDT 100

# ✅ Execute full workflow using symbols
node scripts/swap.js TRX USDT 100 --execute

# ✅ Execute using contract addresses
node scripts/swap.js TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf TYsbWxNnyTgsZaTFaue9hqpxkU3Fkco94a 0.1 --execute

# ✅ Mix symbols and addresses
node scripts/swap.js USDT TYsbWxNnyTgsZaTFaue9hqpxkU3Fkco94a 50 --execute

# 📊 Check balance and allowance only
node scripts/swap.js USDT TRX 50 --check-only

# 📝 Approve only (if needed)
node scripts/swap.js USDT TRX 50 --approve-only --execute

# 🔄 Swap only (assumes already approved)
node scripts/swap.js USDT TRX 50 --swap-only --execute

# 🎯 Custom slippage and network
node scripts/swap.js TRX USDT 100 --execute --slippage 1.0 --network mainnet
```

---

## 🎯 Usage Patterns

### Pattern 1: Quick Execution (One Command)

**Best for:** Automated workflows, trusted operations

```bash
# Execute everything in one command
node scripts/swap.js TRX USDT 100 --execute
```

The script automatically:
1. ✅ Checks balance
2. ✅ Checks allowance  
3. ✅ Gets latest price quote
4. ✅ Approves if needed
5. ✅ Executes swap

**Pros:** Fast, one command
**Cons:** User doesn't see quote before execution

---

### Pattern 2: Two-Step Confirmation (Recommended for AI Agents)

**Best for:** User-facing operations, large amounts

**Step 1: Show quote to user**
```bash
node scripts/quote.js TRX USDT 100
```

Output:
```
Quote: 100 TRX → 15.234 USDT
Price Impact: 0.12%
Route: TRX → WTRX → USDT
```

**Step 2: Execute after user confirms**
```bash
node scripts/swap.js TRX USDT 100 --execute
```

**Why quote twice?**
- First quote: For user decision
- Second quote (inside swap): Gets latest price before execution
- Prices change! This protects against slippage

**Pros:** User sees price before committing
**Cons:** Two commands

---

### Pattern 3: Step-by-Step (Advanced)

**Best for:** Debugging, manual control

```bash
# 1. Check balance
node scripts/balance.js

# 2. Get quote
node scripts/quote.js USDT TRX 50

# 3. Check if approval needed
node scripts/swap.js USDT TRX 50 --check-only

# 4. Approve if needed
node scripts/swap.js USDT TRX 50 --approve-only --execute

# 5. Execute swap
node scripts/swap.js USDT TRX 50 --swap-only --execute
```

---

## 🎯 Recommended Workflow for AI Agents

Use **Pattern 2** for best user experience:

**Step 1: Show user the quote**
```bash
node scripts/quote.js TRX USDT 100
```

**Step 2: Ask for confirmation**
Show the user:
- Amount in/out
- Price impact
- Route
- Estimated gas

**Step 3: Execute if confirmed**
```bash
node scripts/swap.js TRX USDT 100 --execute
```

The script automatically:
- ✅ Checks balance
- ✅ Checks allowance
- ✅ Approves if needed (waits for confirmation)
- ✅ Executes swap
- ✅ Returns transaction hash

---

## 🔐 Security Rules

### 🚨 CRITICAL: Never Display Private Keys

**FORBIDDEN:**
- ❌ Private keys
- ❌ Seed phrases
- ❌ Environment variable values containing keys

**ALLOWED:**
- ✅ Public wallet addresses
- ✅ Transaction hashes
- ✅ Token balances

### 🚨 CRITICAL: Prevent Duplicate Transactions

- One user command = one transaction
- After success, mark as done
- Don't retry successful transactions

### 🚨 CRITICAL: Prevent Self-Transfers

- Validate recipient ≠ wallet address
- Scripts automatically check this

---

## 📊 Script Output Format

All scripts output:
- **JSON to stdout** - For parsing
- **Human-readable to stderr** - For logging

The new **price script** (`scripts/price.js`) follows the same convention:
- JSON result to stdout (safe for programmatic consumption)
- Human-readable summary (price, symbol, currency, timestamp) to stderr

**Example:**
```bash
# Capture JSON output
RESULT=$(node scripts/quote.js TRX USDT 100)

# Parse with jq
echo $RESULT | jq '.amountOut'
```

---

## 🛠 Supported Tokens

All scripts support both:
- **Token symbols** (e.g., TRX, USDT, WTRX) - Must be defined in `resources/common_tokens.json`
- **Contract addresses** (e.g., TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf) - Any valid TRC20 token address

Check `resources/common_tokens.json` for pre-configured tokens on each network.

**Common tokens:**
- **TRX** - Native TRON token (no approval needed)
- **USDT** - Tether USD
- **USDC** - USD Coin
- **USDD** - Decentralized USD
- **WTRX** - Wrapped TRX

**Using custom tokens:**
You can use any token by its contract address, even if it's not in the common tokens list. The scripts will automatically detect it and use default settings (6 decimals).

---

## ⚠️ Common Issues

### "TRON_PRIVATE_KEY not set"
```bash
export TRON_PRIVATE_KEY="your_64_character_hex_key"
```

### "Insufficient balance"
Check balance first:
```bash
node scripts/balance.js
```

Ensure you have:
- Enough tokens for the swap
- At least 100 TRX for gas fees

### "Insufficient allowance"
The swap script handles this automatically with `--execute`.

Or approve manually:
```bash
node scripts/swap.js USDT TRX 50 --approve-only --execute
```

### "Module not found"
Install dependencies:
```bash
cd ~/.openclaw/skills/sunswap
npm install
```

---

## 🎓 User Communication Protocol

When executing swaps, communicate clearly:

**Before execution:**
```
🔍 Getting quote for 100 TRX → USDT...

Quote received:
  100 TRX → 15.234 USDT
  Price Impact: 0.12%
  Route: TRX → WTRX → USDT
  
Proceed with swap? (yes/no)
```

**During execution:**
```
📊 Checking balances...
   TRX: 250.5 ✅
   
🔐 Checking allowance... (skipped for TRX)

💱 Getting final quote...

🔄 Executing swap...
   Transaction sent: abc123...
   
⏳ Waiting for confirmation...
```

**After success:**
```
✅ Swap completed!
   Transaction: abc123def456...
   Explorer: https://nile.tronscan.org/#/transaction/abc123def456...
   
   Swapped: 100 TRX → 15.234 USDT
```

---

## 📖 Examples

### Example 1: Simple TRX → USDT Swap

```bash
# User: "Swap 100 TRX to USDT"

# Step 1: Get quote
node scripts/quote.js TRX USDT 100

# Step 2: Show user and ask confirmation
# (User confirms)

# Step 3: Execute
node scripts/swap.js TRX USDT 100 --execute
```

### Example 2: USDT → TRX with Approval

```bash
# User: "Swap 50 USDT to TRX"

# Step 1: Check if approval needed
node scripts/swap.js USDT TRX 50 --check-only

# Step 2: If needs approval, show quote and ask confirmation
node scripts/quote.js USDT TRX 50

# Step 3: Execute (auto-approves if needed)
node scripts/swap.js USDT TRX 50 --execute
```

### Example 3: Advanced - Manual Steps

```bash
# Check balance first
node scripts/balance.js

# Get quote
node scripts/quote.js TRX USDT 100

# Check if ready
node scripts/swap.js TRX USDT 100 --check-only

# Approve if needed (for TRC20 tokens)
node scripts/swap.js USDT TRX 50 --approve-only --execute

# Execute swap
node scripts/swap.js USDT TRX 50 --swap-only --execute
```

---

## 🔗 Resources

- **Contract Addresses**: `resources/sunswap_contracts.json`
- **Token List**: `resources/common_tokens.json`
- **SunSwap Docs**: https://docs.sun.io/

---

## 🆘 Troubleshooting

### Script fails with "Cannot find module"
```bash
cd ~/.openclaw/skills/sunswap
npm install
```

### "Network error" or "Timeout"
- Check internet connection
- For mainnet, ensure `TRONGRID_API_KEY` is set
- Try again (network might be congested)

### Transaction fails
- Check you have enough TRX for gas (100+ recommended)
- Increase slippage: `--slippage 1.0`
- Check token balance is sufficient

### "Self-transfer detected"
- Don't specify `--recipient` as your own wallet
- Or omit `--recipient` to use your wallet (default)

---

---

## 🌊 SunSwap V2 Liquidity Management

Manage liquidity on SunSwap V2 AMM pools using `scripts/liquidity.js`.

Contract configuration is loaded from `resources/liquidity_manager_contracts.json`.

| Network | V2 Router | V2 Factory |
|---------|-----------|------------|
| **Mainnet** | `TKzxdSv2FZKQrEqkKVgp5DcwEXBEKMg2Ax` | `TKWJdrQkqHisa1X8HUdHEfREvTzw4pMAaY` |
| **Nile** | `TMn1qrmYUMSTXo9babrJLzepKZoPC7M6Sy` | `THomLGMLhAjMecQf9FQjbZ8a1RtwsZLrGE` |

---

### 5. Add Liquidity

```bash
node scripts/liquidity.js add <TOKEN_A> <TOKEN_B> <AMOUNT_A> <AMOUNT_B> [OPTIONS]
```

**Parameters:**
- `TOKEN_A` / `TOKEN_B`: Token symbol (TRX, USDT, …) or TRC20 address
- `AMOUNT_A` / `AMOUNT_B`: Desired amounts (human-readable, e.g. `100`)

**Options:**
- `--network <nile|mainnet>` - Network (default: nile)
- `--slippage <5>` - Slippage tolerance % (default: 5)
- `--execute` - Execute on-chain (without this, dry-run only)
- `--check-only` - Only check balances and allowances (read-only, no private key used)
- `--approve-only` - Only approve tokens (requires `--execute`)

**Step-by-step workflow (same pattern as swap.js):**
1. `--check-only` → Read-only: check reserves, compute optimal amounts, check balances & allowances
2. `--approve-only --execute` → Approve tokens for the router (user confirms this step)
3. `--execute` → Add liquidity (will NOT auto-approve; stops if approval still needed)

**Examples:**
```bash
# Step 1: Check everything (read-only, no private key)
node scripts/liquidity.js add TRX USDT 100 15 --check-only

# Step 2: Approve if needed (user confirms)
node scripts/liquidity.js add TRX USDT 100 15 --approve-only --execute

# Step 3: Execute add liquidity
node scripts/liquidity.js add TRX USDT 100 15 --execute

# Two TRC20 tokens
node scripts/liquidity.js add USDT USDC 100 100 --check-only
node scripts/liquidity.js add USDT USDC 100 100 --approve-only --execute
node scripts/liquidity.js add USDT USDC 100 100 --execute
```

**Output (stdout JSON):**
- `--check-only`: `readyToExecute`, `needsApproval`, balances, optimal amounts
- `--approve-only --execute`: `approved: [{ symbol, transaction }]`
- `--execute` when approval needed: `status: "approval_required"`, `needsApproval: [...]`
- `--execute` on success: `success`, `transaction`, `explorer`, `pool`, `lpGained`, `tokenA`, `tokenB`, `unusedTokens`

---

### 6. Remove Liquidity

```bash
node scripts/liquidity.js remove <TOKEN_A> <TOKEN_B> <LP_AMOUNT> [OPTIONS]
```

**Parameters:**
- `TOKEN_A` / `TOKEN_B`: The two tokens in the pool
- `LP_AMOUNT`: Amount of LP tokens to remove (human-readable, 18 decimals)
- Same `--network`, `--slippage`, `--execute`, `--check-only`, `--approve-only` options as above

**Step-by-step workflow:**
1. `--check-only` → Read-only: check LP balance, compute expected token output, check LP allowance
2. `--approve-only --execute` → Approve LP token for the router (user confirms this step)
3. `--execute` → Remove liquidity (will NOT auto-approve; stops if LP approval still needed)

**Examples:**
```bash
# Step 1: Check everything (read-only)
node scripts/liquidity.js remove TRX USDT 5.5 --check-only

# Step 2: Approve LP token if needed (user confirms)
node scripts/liquidity.js remove TRX USDT 5.5 --approve-only --execute

# Step 3: Execute remove liquidity
node scripts/liquidity.js remove TRX USDT 5.5 --execute
```

**Output (stdout JSON):**
- `--check-only`: `readyToExecute`, `needsApproval`, LP balance, expected token output
- `--approve-only --execute`: `approved: [{ symbol, address, transaction }]`
- `--execute` when approval needed: `status: "approval_required"`, `needsApproval: ["LP"]`
- `--execute` on success: `success`, `transaction`, `explorer`, `pool`, `lpRemoved`, `lpRemaining`, `expectedTokenA`, `expectedTokenB`

---

### Recommended Liquidity Workflow for AI Agents

Follow the **same pattern as swap.js** — each private-key operation requires a separate explicit command with `--execute`.

**Adding liquidity (3-step):**

```bash
# Step 1: Check (read-only, safe to run without user confirmation)
node scripts/liquidity.js add TRX USDT 100 15 --check-only
# → Show user: optimal amounts, unused tokens, whether approval is needed

# Step 2: Approve (only if needed — ask user to confirm first)
node scripts/liquidity.js add TRX USDT 100 15 --approve-only --execute

# Step 3: Add liquidity (ask user to confirm first)
node scripts/liquidity.js add TRX USDT 100 15 --execute
```

**Removing liquidity (3-step):**

```bash
# Step 1: Check (read-only)
node scripts/liquidity.js remove TRX USDT 5.5 --check-only
# → Show user: expected token output, whether LP approval is needed

# Step 2: Approve LP token (only if needed — ask user to confirm first)
node scripts/liquidity.js remove TRX USDT 5.5 --approve-only --execute

# Step 3: Remove liquidity (ask user to confirm first)
node scripts/liquidity.js remove TRX USDT 5.5 --execute
```

**Key principle:** The script **never** auto-approves. Every operation that uses the private key requires a separate explicit `--execute` command. The AI agent must show the user what will happen and get confirmation before running any `--execute` step.

---

## ⚡ SunSwap V3 Position Management (Concentrated Liquidity)

Manage V3 concentrated liquidity positions using `scripts/position.js`.

Contract configuration is loaded from `resources/liquidity_manager_contracts.json`.

| Network | V3 Factory | V3 Position Manager |
|---------|-----------|---------------------|
| **Mainnet** | `TThJt8zaJzJMhCEScH7zWKnp5buVZqys9x` | `TLSWrv7eC1AZCXkRjpqMZUmvgd99cj7pPF` |
| **Nile** | `TLJWAScHZ4Qmk1axyKMzrnoYuu2pSLer1F` | `TPQzqHbCzQfoVdAV6bLwGDos8Lk2UjXz2R` |

**Fee tiers:**

| Fee Rate | Fee Value | Tick Spacing |
|----------|-----------|-------------|
| 0.01%    | 100       | 1           |
| 0.05%    | 500       | 10          |
| 0.3%     | 3000      | 60          |
| 1%       | 10000     | 200         |

---

### 7. Check User Positions

```bash
node scripts/position.js positions [--network nile|mainnet]
```

Enumerates positions directly on-chain via the NonfungiblePositionManager contract (`balanceOf` + `tokenOfOwnerByIndex` + `positions`).

**Output (stdout JSON):** `{ positions: [...], count, source: "onchain" }`

---

### 8. Add / Increase V3 Position

```bash
node scripts/position.js add TOKEN_A TOKEN_B AMT_A AMT_B --fee N --tick-lower N --tick-upper N [OPTIONS]
```

**Parameters:**
- `TOKEN_A` / `TOKEN_B`: Token symbol (TRX, USDT, …) or TRC20 address
- `AMT_A` / `AMT_B`: Desired amounts (human-readable)
- `--fee <100|500|3000|10000>`: Pool fee tier
- `--tick-lower <N>` / `--tick-upper <N>`: Price range ticks (auto-aligned to tick spacing)

**Options:**
- `--network <nile|mainnet>` - Network (default: nile)
- `--slippage <5>` - Slippage tolerance % (default: 5)
- `--execute` - Execute on-chain
- `--check-only` - Read-only check
- `--approve-only` - Only approve tokens (requires `--execute`)
- `--create-pool` - Create pool if it doesn't exist
- `--position-id <N>` - Force increase on a specific position

**Behavior:**
1. Checks pool existence → if missing, reports `pool_not_found` (use `--create-pool --execute` to create)
2. Searches for existing position matching (tokens, fee, ticks) → `mint` if new, `increaseLiquidity` if exists
3. Estimates actual token amounts using V3 liquidity math
4. Checks balances and approvals (tokens must be approved to the PositionManager, including WTRX for TRX)
5. Follows `--check-only` / `--approve-only` / `--execute` pattern (same as V2 liquidity)

**Important:** When TRX is specified, it is auto-substituted to WTRX for V3. The user needs WTRX balance (not TRX).

**Step-by-step workflow:**
```bash
# Step 1: Check (read-only)
node scripts/position.js add TRX USDT 100 15 --fee 3000 --tick-lower -60 --tick-upper 60 --check-only

# Step 2: Approve (user confirms)
node scripts/position.js add TRX USDT 100 15 --fee 3000 --tick-lower -60 --tick-upper 60 --approve-only --execute

# Step 3: Execute (user confirms)
node scripts/position.js add TRX USDT 100 15 --fee 3000 --tick-lower -60 --tick-upper 60 --execute
```

**Output (stdout JSON):**
- `--check-only`: `action`, `poolExists`, `currentTick`, `estimatedLiquidity`, `token0`, `token1`, `needsApproval`, `readyToExecute`
- `--approve-only --execute`: `approved: [{ symbol, transaction }]`
- `--execute`: `success`, `transaction`, `positionId`, `pool`, `tickLower`, `tickUpper`, `fee`

---

### 9. Remove / Decrease V3 Position

```bash
node scripts/position.js remove [TOKEN_A TOKEN_B --fee N --tick-lower N --tick-upper N | --position-id N] [--percent N] [OPTIONS]
```

**Parameters:**
- Identify position by tokens + fee + ticks, OR by `--position-id`
- `--percent <0-100>` - Percentage of liquidity to remove (default: 100 = full removal)

**Behavior:**
1. Finds position (on-chain lookup)
2. Computes estimated token output and remaining position info
3. Executes `decreaseLiquidity` followed by `collect` (two transactions)

**Step-by-step workflow:**
```bash
# Step 1: Check
node scripts/position.js remove --position-id 12345 --percent 50 --check-only

# Step 2: Execute
node scripts/position.js remove --position-id 12345 --percent 50 --execute
```

**Output (stdout JSON):**
- `--check-only`: `positionId`, `percent`, `liquidityToRemove`, `expectedToken0`, `expectedToken1`, `remainingLiquidity`
- `--execute`: `success`, `transactions: { decreaseLiquidity, collect }`, `remainingLiquidity`

---

### 10. Collect V3 Fee Rewards

```bash
node scripts/position.js collect [TOKEN_A TOKEN_B --fee N --tick-lower N --tick-upper N | --position-id N] [OPTIONS]
```

**Parameters:**
- Identify position by tokens + fee + ticks, OR by `--position-id`

**Behavior:**
1. Finds position on-chain
2. Estimates claimable fees via static call to `collect` (using `collectView` ABI with `stateMutability: "view"` to force `triggerConstantContract`). This returns the exact claimable amounts without executing a transaction.
3. If fees > 0, executes `collect` on the PositionManager (using the original `payable` ABI)

**Step-by-step workflow:**
```bash
# Step 1: Check
node scripts/position.js collect --position-id 12345 --check-only

# Step 2: Execute
node scripts/position.js collect --position-id 12345 --execute
```

**Output (stdout JSON):**
- `--check-only`: `positionId`, `claimable`, `fee0`, `fee1`, `readyToExecute`
- `--execute`: `success`, `transaction`, `fee0`, `fee1`

---

### Recommended V3 Position Workflow for AI Agents

Follow the **same pattern as V2 liquidity** — each private-key operation requires explicit `--execute`.

**Adding a V3 position (3-step):**

```bash
# Step 1: Check (read-only, safe to run without confirmation)
node scripts/position.js add USDT USDC 1000 1000 --fee 500 --tick-lower -10 --tick-upper 10 --check-only
# → Show user: pool status, estimated amounts, whether approval is needed

# Step 2: Approve (only if needed — ask user to confirm first)
node scripts/position.js add USDT USDC 1000 1000 --fee 500 --tick-lower -10 --tick-upper 10 --approve-only --execute

# Step 3: Add position (ask user to confirm first)
node scripts/position.js add USDT USDC 1000 1000 --fee 500 --tick-lower -10 --tick-upper 10 --execute
```

**Removing a V3 position (2-step):**

```bash
# Step 1: Check (read-only)
node scripts/position.js remove --position-id 12345 --percent 100 --check-only
# → Show user: expected token output, remaining liquidity

# Step 2: Remove (ask user to confirm first)
node scripts/position.js remove --position-id 12345 --percent 100 --execute
```

**Collecting fees (2-step):**

```bash
# Step 1: Check (read-only)
node scripts/position.js collect --position-id 12345 --check-only
# → Show user: claimable fee amounts

# Step 2: Collect (ask user to confirm first)
node scripts/position.js collect --position-id 12345 --execute
```

**Key principle:** The script **never** auto-approves or auto-executes. Every private-key operation requires explicit `--execute`.

---

**Version**: 2.1.0 (Script-based)  
**Last Updated**: 2026-02-24  
**Maintainer**: Bank of AI Team
