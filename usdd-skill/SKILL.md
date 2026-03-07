---
name: USDD / JUST Protocol
description: USDD stablecoin operations — PSM swaps (buyGem/sellGem), vault position queries, and balance checks via the JUST Protocol on TRON.
version: 1.0.0
dependencies:
  - node >= 18.0.0
  - tronweb
tags:
  - defi
  - stablecoin
  - tron
  - usdd
  - vault
  - cdp
  - just
  - psm
---

# USDD / JUST Protocol

Interact with **USDD**, TRON's over-collateralized stablecoin, via the JUST Protocol. Swap USDT for USDD at 1:1 through the Peg Stability Module (PSM), query vault (CDP) positions and protocol parameters, and check token balances.

---

## Quick Start

```bash
cd usdd-skill && npm install
export TRON_PRIVATE_KEY="<your-private-key>"
export TRON_NETWORK="mainnet"
```

> [!CAUTION]
> **Never display or log the private key.**

---

## Available Scripts

### 1. `psm-swap.js` — Buy/Sell USDT via PSM (1:1, Zero Fee)

```bash
node scripts/psm-swap.js sell 1000 --dry-run    # Preview: 1000 USDT -> 1000 USDD
node scripts/psm-swap.js sell 500                # Execute: sell 500 USDT for USDD
node scripts/psm-swap.js buy 1000 --dry-run      # Preview: spend USDD -> 1000 USDT
node scripts/psm-swap.js buy 250                 # Execute: buy 250 USDT with USDD
```

- `sell <amount>`: Sell USDT to PSM, receive USDD 1:1
- `buy <amount>`: Buy USDT from PSM, spend USDD 1:1
- Amount is always in USDT terms
- Auto-handles TRC20 approval
- Uses the direct `buyGem`/`sellGem` PSM interface (not the router)

> [!NOTE]
> PSM fees (`tin`/`tout`) are currently **0%**. Use `psm-info.js` to verify current fees.

**Output:** `action`, `direction`, `amount_usdt`, `status`, `tx_id`, `needs_approval`

### 2. `psm-info.js` — PSM State (Read-Only)

```bash
node scripts/psm-info.js
```

**No private key required.** Shows PSM fees (tin/tout), USDT reserves held by the GemJoin, and USDD total supply.

**Output:** `fees` (tin, tout, percentages), `reserves` (usdt_available), `usdd` (total_supply)

### 3. `balance.js` — Check Token Balances

```bash
node scripts/balance.js
node scripts/balance.js --address TXYzL2gqz5AB4dbGeiX9h8unkKHxuWwb
```

Queries balances for USDD, USDT, USDC, TRX, and JST. Uses `--address` for read-only lookups (no private key needed).

**Output:** `wallet`, `balances[]` (symbol, balance, address)

### 4. `vault-info.js` — Vault Positions & Parameters (Read-Only)

```bash
node scripts/vault-info.js                      # All vault types
node scripts/vault-info.js --vault TRX-A        # Specific vault type
node scripts/vault-info.js --cdp 42             # Specific CDP position
```

**No private key required.** Queries the Vat and DssCdpManager for vault parameters and individual CDP positions.

Without `--cdp`: shows global parameters per vault type (total debt, rate, spot price, debt ceiling, dust).

With `--cdp <id>`: shows a specific CDP's collateral locked, debt, and collateralization ratio.

**Output (global):** `vaults[]` (name, total_debt_usdd, rate, spot, debt_ceiling_usdd)

**Output (CDP):** `cdp_id`, `owner`, `collateral_locked`, `actual_debt_usdd`, `collateralization_ratio`

---

## Usage Patterns

### Get USDD via PSM (Simplest)

```bash
node scripts/psm-info.js                         # Check PSM reserves and fees
node scripts/psm-swap.js sell 1000 --dry-run      # Preview swap
node scripts/psm-swap.js sell 1000                # Execute: 1000 USDT -> 1000 USDD
```

### Redeem USDD for USDT

```bash
node scripts/balance.js                           # Check USDD balance
node scripts/psm-swap.js buy 500 --dry-run        # Preview redemption
node scripts/psm-swap.js buy 500                  # Execute: spend USDD -> 500 USDT
```

### Inspect Vault Health

```bash
node scripts/vault-info.js                        # View all vault type parameters
node scripts/vault-info.js --cdp 42               # Check specific CDP position
```

---

## Supported Vaults

| Name | Collateral | GemJoin Address | Stability Fee |
|---|---|---|---|
| TRX-A | TRX | `TJ1VWPvFVq7sVsN7J7dWJVZz4SLT14qRUr` | 5% |
| TRX-B | TRX | `TGQKnHDQNyc3QeHJ7YxH8wggdg89UVXyvX` | 5% |
| TRX-C | TRX | `TPUPPLTYLdbW4jxwD5g2T7ystxsR9HL2mt` | 5% |
| sTRX-A | sTRX | `TKha7zcAXZMaaWzoVmUHtvVFqr9GeiChgJ` | 1% |
| USDT-A | USDT | `TDUkQbjrXs6xUbxGCLknWwJHxVTdysXBhy` | 0% |

---

## Key Contracts

| Contract | Address | Description |
|---|---|---|
| USDD Token (v2) | `TXDk8mbtRbXeYuMNS83CfKPaYYT8XWv9Hz` | USDD TRC20 (18 decimals) |
| UsddPsm | `TBXW4hS5KYjjbJXDpnrPf4zhkLwrpUjbyz` | PSM — buyGem/sellGem for 1:1 swaps |
| PSM GemJoin | `TSUYvQ5tdd3DijCD1uGunGLpftHuSZ12sQ` | PSM USDT collateral adapter |
| DssCdpManager | `TDDWjmQaquEtUn1Pa8wCd8dfWFPdQLGPYL` | CDP management (open, frob, flux) |
| Vat | `TH5dhX7o39afSbfDT2e3c9k4itWjNKD4D9` | Core accounting engine |
| USDT Token | `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t` | USDT TRC20 (6 decimals) |
| JST Token | `TCFLL5dx5ZJdKnWuesXxi1VPwjLVmWZZy9` | JUST governance token (18 decimals) |

---

## Security Rules

1. **Never display private keys.**
2. **Always dry-run before PSM swaps.** Verify amounts and token directions.
3. **Check PSM reserves before swapping.** If USDT reserves are low, buyGem may fail.
4. **Decimal mismatch awareness.** USDD is 18 decimals, USDT/USDC are 6. Scripts handle normalization automatically.
5. **Vault positions are read-only.** This skill queries but does not modify vault positions (no deposit/draw/repay/withdraw).
6. **Verify CDP IDs.** Always confirm the CDP ID and owner before acting on position data.

---

## Common Issues

| Problem | Solution |
|---|---|
| `Unknown token` | Use USDD, USDT, USDC, TRX, or JST |
| `Insufficient balance` | Check wallet balance with `balance.js` before swapping |
| PSM swap fails | PSM may be depleted — check reserves with `psm-info.js` |
| `Unknown vault` | Use TRX-A, TRX-B, TRX-C, sTRX-A, or USDT-A |
| `Unknown network` | Set `TRON_NETWORK` to mainnet, nile, or shasta |
| Vault shows all zeros | The ilk may not be active on this network, or the CDP ID does not exist |

---

*Version 1.0.0 — Created by [M2M Agent Registry](https://m2mregistry.io) for Bank of AI*
