---
name: SunPump Meme Token Toolkit
description: Trade meme tokens on SunPump — both pre-launch (bonding curve via `sun sunpump buy/sell`) and post-launch (SunSwap via `sun swap`) — and query token info, rankings, holders, portfolios, and trade history.
version: 1.2.0
dependencies:
  - "@bankofai/sun-cli"
tags:
  - defi
  - meme
  - tron
  - sunpump
  - sunswap
---

# SunPump Meme Token Skill

## Quick Start

This skill enables AI agents to interact with **SunPump** — the meme-token launchpad on the TRON blockchain — through `sun-cli`. It covers the seven core flows an end user needs:

1. **Trade post-launch tokens** through SunSwap (`sun swap`)
2. **Trade pre-launch tokens** on the SunPump bonding curve (`sun sunpump buy` / `sun sunpump sell`)
3. **Check a wallet's positions** (`sun sunpump portfolio`)
4. **View a wallet's trade history** (`sun sunpump tx user`)
5. **Look up token info** (`sun sunpump token get`)
6. **See token rankings** (`sun sunpump token ranking`)
7. **List a token's top holders** (`sun sunpump token holders`)

**Pre-launch vs post-launch decision** — choose the right trade command:

| Token state | `tokenLaunchedInstant` | `swapPoolAddress` | Trade with |
|---|---|---|---|
| Pre-launch (bonding curve) | `null` | `null` | `sun sunpump buy` / `sun sunpump sell` |
| Post-launch (migrated to DEX) | non-null | non-null | `sun swap` |

Always call `sun sunpump state <addr>` or `sun sunpump token get <addr>` first to determine which path to use.

### Prerequisites

> **Wallet required for trading only:** Run `agent-wallet list` first.
> If no wallets exist, invoke `bankofai-guide` (Section C — Wallet Guard) before proceeding.
> All read-only SunPump queries (portfolio, tx history, token info, ranking, holders) work without a wallet.

1. **Install this skill** (once, picked up by Claude Code / Cursor / Codex):
   ```bash
   # After PR is merged to main:
   npx skills add BofAI/skills --skill sunpump-agent-skill -g -a claude-code -y

   # Pre-merge (branch-pinned):
   npx skills add https://github.com/BofAI/skills/tree/sunpump-add/sunpump-agent-skill -g -a claude-code -y
   ```
   If Claude Code can't see it after a global install, symlink (vercel-labs/skills [#851](https://github.com/vercel-labs/skills/issues/851)):
   ```bash
   ln -s ~/.agents/skills/sunpump-agent-skill ~/.claude/skills/sunpump-agent-skill
   ```

2. **Install sun-cli** (≥ 1.2.0 required — earlier versions lack `sunpump buy/sell/state`):
   ```bash
   npm install -g @bankofai/sun-cli@^1.2.0
   ```

3. **Configure wallet** (required for write commands — `sun swap`, `sun sunpump buy`, `sun sunpump sell`):
   ```bash
   export TRON_PRIVATE_KEY="your_private_key_here"
   ```
   Alternative wallet sources: `TRON_MNEMONIC` or `AGENT_WALLET_PASSWORD`.

4. **Optional environment variables:**
   ```bash
   export TRON_NETWORK=mainnet         # SunPump is mainnet only
   export TRONGRID_API_KEY=your_key
   export SUNPUMP_API_BASE_URL=...     # override the API host if needed
   ```

---

## AI Agent Flags

Always use these flags when calling `sun` from an AI agent:

| Flag | Purpose |
|------|---------|
| `--json` | Machine-readable JSON output to stdout |
| `--yes` | Skip interactive confirmation prompts (write commands only) |
| `--dry-run` | Simulate write operations without sending transactions |
| `--fields` | Limit output to specific comma-separated fields |
| `--network` | Must be `mainnet` for SunPump — any other value is rejected fast |

Standard agent invocation pattern (read-only):

```bash
sun --json sunpump token get TXYZ...
```

Write operation (swap) with explicit confirmation skip:

```bash
sun --json --yes swap TRX TXYZ... 100000000
```

> **WARNING: SunPump is mainnet only.**
> Endpoint: `https://api-v2.sunpump.meme/pump-api`. The CLI throws
> `SunPump is only available on mainnet (got "...")` for any other `--network` value
> (including `nile` and `shasta`). Drop `--network` or pass `--network mainnet`.

---

## Command Reference

### 1. Post-launch Trading — `sun swap`

Once a SunPump token migrates to SunSwap (`tokenLaunchedInstant` non-null, `swapPoolAddress` set), it trades through the SunSwap Universal Router. Use the same `sun swap` and `sun swap:quote` commands as for any TRC20 pair.

**Parameters:** `tokenIn` and `tokenOut` accept symbols (TRX, USDT) or TRC20 contract addresses. `amountIn` is in sun (smallest unit — for TRX, 1 TRX = 1_000_000). `--slippage` is a decimal (default `0.005` = 0.5%).

#### Step A — Get a quote (read-only, no wallet)

```bash
sun --json swap:quote TRX TXYZ1234567890abcdefghijklmnopqrstuv 100000000
```

Show the user: `amountOut`, price impact, and route.

#### Step B — Buy (TRX → meme token)

```bash
sun --json --yes swap TRX TXYZ1234567890abcdefghijklmnopqrstuv 100000000 --slippage 0.01
```

#### Step C — Sell (meme token → TRX)

```bash
sun --json --yes swap TXYZ1234567890abcdefghijklmnopqrstuv TRX 1000000000000000000 --slippage 0.01
```

> **NOTE:** Meme-token decimals vary. Resolve the token's `decimals` via `sun sunpump token get <address>` before computing `amountIn`.

#### Dry-run first for large trades

```bash
sun --json --yes --dry-run swap TRX TXYZ... 1000000000
```

> **WARNING: `--dry-run` only previews the transaction structure.**
> It does NOT check balances, validate that the pool exists, or reject same-token swaps.
> See [Agent Pre-Validation Checklist](#agent-pre-validation-checklist).

#### Pre-launch tokens (bonding curve, not yet on SunSwap)

A token whose `tokenLaunchedInstant` is null is still on the SunPump bonding curve and **cannot** be traded through `sun swap`. Use the pre-launch trading commands in [Section 2](#2-pre-launch-trading--sun-sunpump-buy--sun-sunpump-sell) instead. Higher slippage (1–5%) is often required for low-liquidity meme pools.

---

### 2. Pre-launch Trading — `sun sunpump buy` / `sun sunpump sell`

For tokens still on the SunPump bonding curve (`tokenLaunchedInstant == null`, or on-chain state `TRADING`/`READY_TO_LAUNCH`), trade directly through the SunPump router contract. These commands handle TRC20 approval automatically on first sell, and accept human-readable decimal inputs (CLI scales TRX × 1e6 and tokens × 10^decimals before calling the contract).

#### Step A — Verify the token is still on the bonding curve

```bash
sun --json sunpump state TXYZ1234567890abcdefghijklmnopqrstuv
```

Returns `{state, info: {tokenAddress, launched, price, trxReserve, tokenReserve}}` where `state` is one of:

| Value | Label | Tradeable via `sun sunpump buy/sell`? |
|---|---|---|
| `0` | `NOT_EXIST` | No (token unknown to SunPump) |
| `1` | `TRADING` | Yes |
| `2` | `READY_TO_LAUNCH` | Yes (bonding curve full, about to migrate) |
| `3` | `LAUNCHED` | No — use `sun swap` |

> **IMPORTANT:** `sun-kit`'s TypeScript enum lists only 0–2, but the on-chain contract returns 3 for fully-launched tokens. The CLI maps 3 → `LAUNCHED`; trust the printed label, not the raw number.

#### Step B — Get a quote (read-only, no wallet)

```bash
sun --json sunpump quote-buy  TXYZ... --trx 10
sun --json sunpump quote-sell TXYZ... --amount 1000
```

Buy returns `{tokenAmount, fee}` in base units. Sell returns `{trxAmount, fee}` in Sun. Both ignore on-chain state — a quote succeeding does **not** mean a trade will succeed. Always check `state` first.

#### Step C — Buy (TRX → meme token)

```bash
sun --json --yes sunpump buy TXYZ... --trx 10
sun --json --yes sunpump buy TXYZ... --trx 10 --slippage 0.1            # 10% slippage
sun --json --yes sunpump buy TXYZ... --trx 10 --min-out 27955000000000000000000  # exact floor in raw units
```

| Flag | Description |
|------|-------------|
| `--trx <amount>` | TRX to spend, **decimal** (e.g. `10` or `1.5`) — CLI scales to Sun internally |
| `--slippage <n>` | Slippage tolerance as decimal (default `0.05` = 5%; meme tokens are volatile) |
| `--min-out <raw>` | Minimum tokens out in raw base units, overrides slippage |

Returns: `{txResult, tokenAddress, trxSpent, expectedTokens, minTokenOut, tronscanUrl}`.

#### Step D — Sell (meme token → TRX)

```bash
sun --json --yes sunpump sell TXYZ... --amount 1000
sun --json --yes sunpump sell TXYZ... --amount 1000 --decimals 6        # non-18-decimal token
sun --json --yes sunpump sell TXYZ... --amount 1000 --slippage 0.1
```

| Flag | Description |
|------|-------------|
| `--amount <amount>` | Tokens to sell, **decimal** (e.g. `1000` or `12.5`) |
| `--decimals <n>` | Token decimals (default `18`; resolve from `sun sunpump token get` if unsure) |
| `--slippage <n>` | Slippage tolerance as decimal (default `0.05` = 5%) |
| `--min-out <raw>` | Minimum TRX out in Sun, overrides slippage |

Returns: `{txResult, tokenAddress, tokensSold, expectedTrx, minTrxOut, tronscanUrl}`.

**First-time sell**: the SDK auto-sends a TRC20 `approve(SunPump, 2^256-1)` before the actual sell tx if allowance is insufficient. Only the final sell tx hash is returned in `tronscanUrl`.

#### Dry-run before execution

```bash
sun --json --yes --dry-run sunpump buy  TXYZ... --trx 10
sun --json --yes --dry-run sunpump sell TXYZ... --amount 1000
```

Prints the resolved parameters (TRX/Sun scaling, computed `minOut`, slippage, network) without broadcasting. Useful for showing the user exactly what will be sent.

#### Network

SunPump is **mainnet only**. The CLI rejects any non-mainnet `--network` value with
`SunPump is only available on mainnet (got "...")`. Router contract:
`TTfvyrAz86hbZk5iDpKD78pqLGgi8C7AAw`.

---

### 3. User Position Check — `sun sunpump portfolio`

List all SunPump-tracked tokens held by a wallet, including TRX-denominated value and portfolio weight.

```bash
sun --json sunpump portfolio TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW
```

Options:

| Flag | Description |
|------|-------------|
| `--include-zero` | Include zero-balance tokens |
| `--min-trx <amount>` | Minimum TRX-equivalent value to include |
| `--page <n>` / `--size <n>` | Pagination |
| `--sort <field>` | Sort field (e.g. `valueInTrx,desc`) |

#### Common patterns

Top 20 positions worth at least 100 TRX:

```bash
sun --json sunpump portfolio TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW --min-trx 100 --size 20 --sort valueInTrx,desc
```

Default table columns: `Symbol | Address | Balance | Price (TRX) | Value (TRX) | Percent`.

---

### 4. Trade History — `sun sunpump tx user`

List a wallet's SunPump swap activity. Each row is one buy or sell on the SunPump bonding curve or its SunSwap pool.

```bash
sun --json sunpump tx user TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW --size 20
```

Filter options:

| Flag | Description |
|------|-------------|
| `--swap-type <BUY\|SELL>` | Direction filter |
| `--pool <address>` | Specific swap pool |
| `--tx-hash <hash>` | Single transaction lookup |
| `--block <n>` | Filter by block number |
| `--start-time <epoch>` / `--end-time <epoch>` | Time range (epoch **seconds**) |
| `--page <n>` / `--size <n>` | Pagination |
| `--sort <field>` | Sort field (e.g. `txDateTime,desc`) |

#### Common patterns

Last 20 buys only:

```bash
sun --json sunpump tx user TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW --swap-type BUY --size 20
```

Trades for one wallet in a window:

```bash
sun --json sunpump tx user TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW --start-time 1747699200 --end-time 1747785600 --size 50
```

> **NOTE:** `--start-time` / `--end-time` are epoch **seconds**, not milliseconds. Convert ISO dates with `date -j -f "%Y-%m-%d" "2026-05-20" +%s` (macOS) or `date -d "2026-05-20" +%s` (Linux).

Default table columns: `Time | Type | From → To | Volume | TxHash`.

---

### 5. Token Info — `sun sunpump token get`

Fetch full metadata for a SunPump token by its contract address. Returns price, market cap, 24h volume, holder count, total supply, owner, swap pool address, social links, and launch state.

```bash
sun --json sunpump token get TXYZ1234567890abcdefghijklmnopqrstuv
```

In human-readable mode (without `--json`), the CLI prints a labelled detail view; in JSON mode it returns the raw token object.

#### Fields to read

| Field | Meaning |
|-------|---------|
| `contractAddress` | TRC20 address of the meme token |
| `symbol`, `name`, `description` | Display metadata |
| `priceInTrx`, `priceInUsd` | Current price |
| `marketCap`, `volume24Hr` | Market metrics (USD) |
| `priceChange24Hr` | 24h price change (decimal, e.g. `0.18` = +18%) |
| `holders`, `totalSupply` | Distribution stats |
| `tokenCreatedInstant` | Bonding-curve creation time |
| `tokenLaunchedInstant` | SunSwap launch time (null if not yet launched) |
| `swapPoolAddress` | Pool to trade through (null pre-launch) |
| `pumpPercentage` | Bonding curve fill % (pre-launch only) |
| `ownerAddress` | Creator's wallet |
| `websiteUrl`, `twitterUrl`, `telegramUrl`, `listOn` | Social and CEX listings |

#### Limit output for low-context responses

```bash
sun --json --fields symbol,priceInUsd,marketCap,volume24Hr,priceChange24Hr sunpump token get TXYZ...
```

---

### 6. Ranking — `sun sunpump token ranking`

Get the top SunPump tokens by a chosen metric. **`--type` is required.**

```bash
sun --json sunpump token ranking --type MARKET_CAP --size 10
```

Valid `--type` values (case-sensitive):

| Value | Meaning |
|-------|---------|
| `MARKET_CAP` | Largest tokens by market capitalization |
| `VOLUME_24H` | Highest 24-hour trading volume |
| `PRICE_CHANGE_24H` | Top 24-hour price gainers |

> **IMPORTANT:** Other type values are rejected by the API. Always validate `--type` before calling.

Options:

| Flag | Description |
|------|-------------|
| `--size <n>` | Number of entries (default depends on server, typical max 50) |

#### Common patterns

Top 10 by market cap:

```bash
sun --json sunpump token ranking --type MARKET_CAP --size 10
```

Top 10 by 24h volume:

```bash
sun --json sunpump token ranking --type VOLUME_24H --size 10
```

Top 10 24h gainers:

```bash
sun --json sunpump token ranking --type PRICE_CHANGE_24H --size 10
```

Default table columns: `Symbol | Name | Address | Price | MCap | Volume24h`.

---

### 7. Top Holders — `sun sunpump token holders`

List the top wallets holding a given SunPump token, with balance and percentage.

```bash
sun --json sunpump token holders TXYZ1234567890abcdefghijklmnopqrstuv --size 20
```

Options:

| Flag | Description |
|------|-------------|
| `--include-zero` | Include zero-balance wallets |
| `--page <n>` / `--size <n>` | Pagination |
| `--sort <field>` | Sort field (default: balance descending) |

Default table columns: `Holder | Type | Balance | Percent`.

> **NOTE:** The `percent` field on the holders endpoint is already a percent value (e.g. `38.51` = 38.51%), whereas the token-list endpoint returns it as a fraction (e.g. `0.3851` = 38.51%). The CLI auto-detects which form it is — but if you read the raw JSON, check the magnitude before interpreting.

If `holders` results look thin, also call `sunpump token get <address>` and read the `holders` field for the total count.

---

## Agent Pre-Validation Checklist

Before executing any **write** operation (`sun swap`, `sun sunpump buy`, `sun sunpump sell`), the AI agent **must** perform these checks:

### Step 0 — Decide which trade path to use

```bash
sun --json sunpump state <memeTokenAddress>
```

- `state == 0` (`NOT_EXIST`) → abort: token unknown to SunPump
- `state == 1` (`TRADING`) or `2` (`READY_TO_LAUNCH`) → use `sun sunpump buy`/`sell`
- `state == 3` (`LAUNCHED`) → use `sun swap`

### Before `sun sunpump buy` / `sun sunpump sell` (pre-launch path)

1. **Check TRX balance is sufficient** for `--trx` plus gas reserve (≥1 TRX recommended):
   ```bash
   sun --json wallet balances
   ```

2. **For sells**, confirm token balance ≥ `--amount`. The SunPump portfolio API may not yet include the token; query the TRC20 balance directly:
   ```bash
   sun --json contract read <tokenAddress> balanceOf --args "[\"<walletAddress>\"]"
   ```

3. **Resolve token decimals before passing `--amount`** for sell. Decimals default to 18 but can differ:
   ```bash
   sun --json sunpump token get <memeTokenAddress>  # read decimals
   sun --json --yes sunpump sell <token> --amount 1000 --decimals <n>
   ```

4. **Validate slippage** is in range 0.005–0.10 (0.5%–10%). Default is 5%, which suits meme tokens; reject anything outside this band without user confirmation.

5. **`--network` must be `mainnet`.** The CLI throws immediately on any other value.

### Before `sun swap` (post-launch path)

1. **Check balance is sufficient:**
   ```bash
   sun --json wallet balances
   ```
   Compare the token balance against `amountIn`. Abort if insufficient.

2. **Verify the token is launched:**
   ```bash
   sun --json sunpump token get <memeTokenAddress>
   ```
   `tokenLaunchedInstant` must be non-null and `swapPoolAddress` must be set. If pre-launch, route to the `sun sunpump buy`/`sell` path instead.

3. **Verify tokenIn ≠ tokenOut.** Same-token swaps are not rejected by `--dry-run`.

4. **Validate slippage is reasonable.** Meme tokens often need 1–5% slippage; flag anything outside 0.001 (0.1%) – 0.10 (10%) for review.

5. **Validate `--network`**. `sun swap` accepts `mainnet` / `nile` / `shasta` for general TRC20 pairs, but SunPump-migrated tokens are still mainnet-only — check the migration target before quoting on a non-mainnet network.

### Before Read-Only Calls

- Validate `--type` for `token ranking` is `MARKET_CAP`, `VOLUME_24H`, or `PRICE_CHANGE_24H`.
- Convert any user-provided dates to epoch **seconds** (not ms) before passing to `tx user --start-time / --end-time`.
- Verify the address is a TRON base58 (`T...`, 34 chars). Bad addresses return empty results or an opaque API error.

---

## Recommended Workflows

### Pattern 1 — Buy a Meme Token (auto-routes pre/post-launch)

**Step 1 — Determine the trade path:**

```bash
sun --json sunpump state TXYZ...
```

- `state == 3` (`LAUNCHED`) → follow [Pattern 1a](#pattern-1a--post-launch-buy-via-sun-swap)
- `state == 1` or `2` (still bonding) → follow [Pattern 1b](#pattern-1b--pre-launch-buy-via-sun-sunpump-buy)
- `state == 0` (`NOT_EXIST`) → abort

Also pull metadata for the user-facing preview:

```bash
sun --json sunpump token get TXYZ...
```

Show the user: price, 24h change, market cap, holders, plus the top-5-holder concentration warning if applicable.

#### Pattern 1a — Post-launch buy via `sun swap`

```bash
sun --json swap:quote TRX TXYZ... 100000000             # quote (no wallet)
sun --json wallet balances                              # check funds
sun --json --yes swap TRX TXYZ... 100000000 --slippage 0.01
```

#### Pattern 1b — Pre-launch buy via `sun sunpump buy`

```bash
sun --json sunpump quote-buy TXYZ... --trx 10           # quote (no wallet)
sun --json wallet balances                              # check funds
sun --json --yes sunpump buy TXYZ... --trx 10           # default 5% slippage
```

Inputs are **decimal**: `--trx 10` means 10 TRX, not 10 Sun. Default slippage is `0.05` (5%) — meme bonding-curve trades move fast. Use `--slippage 0.005` to tighten, or `--min-out <raw>` to lock a floor in base units.

---

### Pattern 2 — Sell a Position (auto-routes pre/post-launch)

**Step 1 — List the user's positions:**

```bash
sun --json sunpump portfolio TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW --min-trx 1 --size 50
```

**Step 2 — User picks a token. Determine path:**

```bash
sun --json sunpump state TXYZ...
sun --json sunpump token get TXYZ...        # also read `decimals` for sell amount scaling
```

#### Pattern 2a — Post-launch sell via `sun swap`

```bash
sun --json swap:quote TXYZ... TRX <amountInSmallestUnits>
sun --json --yes swap TXYZ... TRX <amount> --slippage 0.02
```

#### Pattern 2b — Pre-launch sell via `sun sunpump sell`

```bash
sun --json sunpump quote-sell TXYZ... --amount 1000 --decimals 18
sun --json --yes sunpump sell TXYZ... --amount 1000 --decimals 18
```

First sell of a given token triggers an automatic TRC20 `approve` tx — only the final sell tx hash is returned.

---

### Pattern 3 — Discover and Research

**Top gainers right now:**

```bash
sun --json sunpump token ranking --type PRICE_CHANGE_24H --size 10
```

**Inspect one:**

```bash
sun --json sunpump token get TXYZ...
```

**Check holder concentration:**

```bash
sun --json sunpump token holders TXYZ... --size 20
```

A few wallets holding >50% combined is a red flag — surface this to the user.

---

### Pattern 4 — Audit a Wallet

**Current holdings:**

```bash
sun --json sunpump portfolio T... --min-trx 1 --sort valueInTrx,desc --size 50
```

**Recent trades:**

```bash
sun --json sunpump tx user T... --size 20 --sort txDateTime,desc
```

**Filter to buys only:**

```bash
sun --json sunpump tx user T... --swap-type BUY --size 20
```

---

## Security Rules

### CRITICAL: Never Display Private Keys

**FORBIDDEN:** private keys, seed phrases, mnemonics, env-var values that contain secrets, agent-wallet passwords.

**ALLOWED:** public wallet addresses, transaction hashes, token balances, prices.

### CRITICAL: Always Preview Before Trading

The AI agent **must never** execute `sun swap` or `sun sunpump buy/sell` without first showing the user a preview. Correct sequence (both paths):

1. `sun --json sunpump state <address>` — determine trade path (pre/post-launch)
2. `sun --json sunpump token get <address>` — show metadata, holder concentration, decimals
3. Quote — `sun --json swap:quote ...` **or** `sun --json sunpump quote-buy/sell ...` — show expected output, fee, price impact
4. `sun --json wallet balances` — confirm sufficient funds
5. **Ask the user to confirm**
6. Execute with `--yes`: `sun --json --yes swap ...` **or** `sun --json --yes sunpump buy/sell ...`

> **WARNING:** Do not pass `--yes` on the first call. Use `--yes` only after the user has reviewed the preview and confirmed.

### CRITICAL: Prevent Duplicate Transactions

- One user command = one transaction
- After a successful swap, mark it as done
- Never silently retry a successful transaction

### CRITICAL: Highlight Holder Concentration

Meme tokens are vulnerable to rug pulls. When surfacing token info to the user, also surface holder concentration. If the top 5 holders combined hold >40% of supply, warn the user explicitly.

---

## User Communication Protocol

**Before a swap:**

```
Token: PEPE (TXYZ...)
  Price: $0.000123  •  24h: +18.4%  •  MCap: $2.4M  •  Holders: 1,420
  Top 5 hold: 31.2%

Quote: 100 TRX → 812,344 PEPE
  Route: TRX → WTRX → PEPE
  Price Impact: 0.42%
  Slippage tolerance: 1%

Proceed with buy?
```

**After success:**

```
Swap completed.
  Transaction: abc123...
  Explorer:    https://tronscan.org/#/transaction/abc123...
  Bought:      100 TRX → 812,344 PEPE
```

---

## Known Limitations

| Issue | Affected Commands | Behavior | Agent Workaround |
|-------|-------------------|----------|------------------|
| `--dry-run` doesn't check balances | `swap` | Returns preview even if balance is insufficient | Check `wallet balances` first |
| Same-token swap not rejected | `swap` | Accepts TRX→TRX in dry-run | Verify tokenIn ≠ tokenOut before calling |
| Pre-launch tokens not on SunSwap | `swap` against a SunPump token | Pool doesn't exist; swap will fail on-chain | Use `sun sunpump buy/sell` instead — verify via `sunpump state` |
| `sunpump quote-buy/sell` ignores state | `sunpump quote-*` | Returns a price even on LAUNCHED tokens (quote-sell may revert) | Always call `sunpump state` before quoting |
| sun-kit enum mislabels state 2 vs 3 | `sunpump.buyToken/sellToken` internal check | TS enum says `LAUNCHED=2` but contract returns 3 for launched | CLI relabels: trust the printed `LAUNCHED (3)` label, not raw int |
| First sell needs TRC20 approve | `sunpump sell` | Two on-chain txs (approve + sell), only sell tx hash returned | Expected; subsequent sells use cached `MaxUint256` allowance |
| SunPump is mainnet only | All `sunpump` subcommands | CLI throws `SunPump is only available on mainnet` on any other `--network` | Drop `--network` or pass `--network mainnet`; the nile/shasta API hosts aren't publicly reachable |
| Invalid `--type` for ranking | `token ranking` | API rejects with non-obvious error | Only pass `MARKET_CAP`, `VOLUME_24H`, or `PRICE_CHANGE_24H` |
| `--start-time` / `--end-time` are seconds, not ms | `tx user`, `tx token` | Ms values produce empty results | Use epoch seconds |
| `percent` field magnitude differs by endpoint | `token holders` vs `token list` | Holders endpoint returns 38.51, list endpoint returns 0.3851 | The CLI normalizes, but check magnitude when consuming raw JSON |

---

## Troubleshooting

### "sun: command not found"
```bash
npm install -g @bankofai/sun-cli
```

### Empty results from a SunPump query
- Confirm the address is a valid TRON base58 (`T...`, 34 chars)
- Try the same command without filters to isolate which option excludes everything
- For `tx user` time windows, confirm timestamps are epoch **seconds**

### Swap fails on a SunPump token
- Run `sun sunpump state <address>` first. If state is `1` (`TRADING`) or `2` (`READY_TO_LAUNCH`), use `sun sunpump buy/sell` — not `sun swap`.
- If state is `3` (`LAUNCHED`) and `swap` still fails, try increasing `--slippage` (meme pools often need 1–5%).
- Ensure ≥ 100 TRX for gas in the wallet.

### `sun sunpump buy/sell` fails with `SUNPUMP_LAUNCHED`
The token has already migrated to SunSwap. Switch to `sun swap`.

### `sun sunpump sell` quote-sell reverts
The token is in state 3 (LAUNCHED). The bonding-curve contract refuses sells once a token has migrated. Use `sun swap` instead.

### "Wallet not configured" (write commands only)
Set one of `TRON_PRIVATE_KEY`, `TRON_MNEMONIC`, or `AGENT_WALLET_PASSWORD`. Read-only sunpump commands do **not** need a wallet.

### Network error / timeout
- Check internet
- For mainnet, set `TRONGRID_API_KEY`
- SunPump itself is mainnet-only — testnet API host is internal-only and not publicly reachable

---

**Version**: 1.2.0 (drops nile testnet — SunPump is now mainnet-only)
**Last Updated**: 2026-05-22
**Maintainer**: Bank of AI Team
