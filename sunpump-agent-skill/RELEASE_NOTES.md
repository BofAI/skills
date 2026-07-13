# Release Notes — SunPump Meme Token Toolkit

## v1.4.0 — 2026-07-09 _(docs only)_

> **TL;DR** — Runtime package moved to `@sun-protocol/sun-cli`.
> This skill now requires `@sun-protocol/sun-cli >= 1.2.2`, which keeps
> `sunpump launch`, bonding-curve trading, and `--dry-run` previews aligned
> with the migrated SUN.IO tooling.

### Changes

- **Runtime dependency scope changed** from the legacy sun-cli package scope
  to `@sun-protocol/sun-cli`.
- **Install command updated**:
  ```bash
  npm install -g @sun-protocol/sun-cli@^1.2.2
  ```
- **Wallet guidance clarified**: read-only SunPump queries, `sunpump launch`,
  and `--dry-run` previews do not need wallet credentials. Real trades still
  require a wallet.
- **Network guidance unchanged**: all `sunpump` subcommands remain mainnet-only.
- **Holder pagination documented**: `token holders` and `holders-v2` honor
  `--page`, but the SunPump API may force page size to 10 regardless of `--size`.

---

## v1.3.1 — 2026-06-08 _(docs only)_

> **TL;DR** — Sync with `@sun-protocol/sun-cli` dropping SunPump nile support
> again: **`sun sunpump launch` is mainnet-only**, like every other
> `sunpump` subcommand. No skill behaviour changes — just makes the
> launch section's network requirement explicit.

### Changes

- **Section 8 (Token Creation)** gains a mainnet-only warning. The
  `sunpump` command group runs a `preAction` guard that throws
  `SunPump is only available on mainnet (got "...")` for any non-mainnet
  `--network`, on every subcommand including `launch`.
- **Clarified the guard fires before the action** — so it applies even
  under `--dry-run` (`--dry-run --network nile` errors out before
  previewing). Drop `--network` or pass `--network mainnet`.
- **Launch pre-validation checklist** adds a `--network` must-be-mainnet
  step.

> The rest of the skill already documented SunPump as mainnet-only (since
> v1.2.0); this release only closes the gap in the launch-specific
> sections.

---

## v1.3.0 — 2026-06-04

> **TL;DR** — Adds **token creation**: `sun sunpump launch` creates a new
> meme token through the SunPump agent endpoint
> (`POST /ai/agentTokenLaunch`). Creation is **server-side** — the platform
> signs and broadcasts the creation transaction, so **no wallet is needed**.
> Requires `@sun-protocol/sun-cli ≥ 1.2.1`.

### Highlights

- **New flow #1 — Create (launch) a token.**
  ```bash
  sun --json --yes sunpump launch \
    --name "My Meme" --symbol MEME \
    --description "The dankest meme on TRON" \
    --image ./logo.png
  ```
  Required: `--name`, `--symbol`, `--description`. Optional:
  `--image <path>` (read and sent as base64) / `--image-base64 <data>`,
  `--twitter-url`, `--telegram-url`, `--website-url`, `--tweet-username`.
  Returns the full token object including `contractAddress`,
  `createTxHash`, and `logoUrl`. The new token starts on the bonding
  curve (state `1 TRADING`) and is immediately buyable via
  `sun sunpump buy`.
- **Honours the standard agent flags** — `--dry-run` prints the resolved
  payload without calling the API; `--yes` skips the interactive
  confirmation; `--json` returns the raw token object.
- **Pre-validation checklist extended** with a launch section: confirm
  name/symbol/description with the user, require a logo, check for
  symbol collisions via `sunpump token search`, dry-run first, launch
  exactly once.
- **Security rules extended** — token creation is irreversible; preview
  and explicit user confirmation are mandatory, and ambiguous launch
  errors must be checked with `sunpump token search <symbol>` before any
  retry (the token may already exist).

### Known quirks (documented in SKILL.md)

| Quirk | Behavior | Workaround |
|-------|----------|------------|
| Launch without a logo | Opaque server error `Invoke third part error` | Always pass `--image <path>` (or `--image-base64`) |
| `*Instant` fields in `--json` launch output | Epoch-millis ÷ 1e6 (e.g. `1780476.327`), not epoch seconds | Multiply by 1000 for epoch seconds; CLI normalizes only in human mode |

### Compatibility

- **Required runtime:** `@sun-protocol/sun-cli ≥ 1.2.1` (earlier versions
  lack `sunpump launch`).
- **Wallet:** unchanged for trading; `sunpump launch` itself needs **no
  wallet** (server-side creation).

### Install / upgrade

```bash
# 1. Install the skill (Claude Code / Cursor / Codex pick it up)
npx skills add BofAI/skills

# 2. Install / upgrade the runtime CLI
npm install -g @sun-protocol/sun-cli@^1.2.1
```

---

## v1.2.0 — 2026-05-22

> **TL;DR** — SunPump is now **mainnet-only**. Any agent that hard-coded
> `--network nile` (or any non-mainnet value) on a `sun sunpump *` command
> must drop the flag or pass `--network mainnet`. The upstream `sun-cli`
> SunPump API surface was also trimmed; only the trading + discovery
> commands remain.

### Highlights

- **Mainnet-only enforcement.** The runtime CLI now fast-fails every
  `sunpump` subcommand when `--network` is anything other than `mainnet`
  with a clear error:
  `SunPump is only available on mainnet (got "...")`.
- **Docs in lockstep.** The README network section, `SKILL.md`
  pre-validation checklist, AI agent flag table, trade examples, and
  troubleshooting guide were all rewritten — no more references to nile
  testnet, "silent fallback", or shasta.
- **Slimmer API surface.** Endpoints that didn't fit the
  trading + discovery loop have been removed in `@sun-protocol/sun-cli`.
  Agents calling any of the removed groups (see below) need to be
  updated.

### Breaking Changes

#### 1. Dropped nile testnet support

**Why:** the SunPump nile API host
(`https://tn-api.sunpump.meme/pump-api`) is internal-only and not
publicly reachable, so any agent passing `--network nile` was previously
hitting an unreachable host.

| Before                                  | After                                                       |
|-----------------------------------------|-------------------------------------------------------------|
| `sun --json sunpump state T... --network nile`     | `sun --json sunpump state T...` (or `--network mainnet`)    |
| Silent fallback / timeout                          | Hard error: `SunPump is only available on mainnet (got "nile")` |

The mainnet router contract is unchanged:
`TTfvyrAz86hbZk5iDpKD78pqLGgi8C7AAw`.

#### 2. Upstream `sun-cli` SunPump command groups removed

The following `sun sunpump *` subcommands were removed in `@sun-protocol/sun-cli ≥ 1.2.0` and are **no longer documented** in this skill:

- `sunpump home` — `stats` / `data` / `banners`
- `sunpump tx ticker` — server-capped at ~15 rows anyway
- `sunpump kline` — v1 / v2 / v3
- `sunpump red-packet` — `get` / `remain` / `by-user` / `summary`
- `sunpump campaign` — `list` / `banners`
- `sunpump referral` — `rewards` / `invites`
- `sunpump admin-summary`
- `sunpump quota`

**Remaining surface** (what the skill targets and what `sun-cli` still
ships):

```
token            tx token   tx user      portfolio
state            quote-buy  quote-sell   buy        sell
```

### Migration Guide

| If your agent did this…                          | Do this instead                                |
|--------------------------------------------------|------------------------------------------------|
| `sun ... sunpump <cmd> --network nile`           | Drop `--network` or use `--network mainnet`    |
| `sun --json sunpump home stats`                  | Removed — no replacement (data not exposed)    |
| `sun --json sunpump kline ...`                   | Removed — pull candles from a market data API  |
| `sun --json sunpump red-packet ...`              | Removed — promotion endpoints retired          |
| `sun --json sunpump campaign list`               | Removed — promotion endpoints retired          |
| `sun --json sunpump referral rewards <addr>`     | Removed                                        |
| `sun --json sunpump admin-summary`               | Removed                                        |
| `sun --json sunpump quota`                       | Removed                                        |
| `sun --json sunpump tx ticker`                   | Use `sun --json sunpump tx token <addr>` instead |

### Documentation Updates

- **Quick-start prerequisites** — `TRON_NETWORK` comment drops the
  "or nile" hint.
- **AI agent flag table** — `--network` documented as mainnet-only for
  SunPump.
- **Pre-launch trading section** — drops the "Network selection"
  example.
- **Pre-validation checklist** — explicitly requires `--network mainnet`
  (or none) and notes the CLI's fast-fail behaviour.
- **Known Limitations table** — replaces the legacy "silently falls back
  to mainnet" and "Shasta unsupported" rows with a single
  "mainnet only" row.
- **Troubleshooting** — removes the "try the nile testnet" suggestion.

### Compatibility

- **Required runtime:** `@sun-protocol/sun-cli ≥ 1.2.0`
- **Wallet:** unchanged — only `swap` / `sunpump buy` / `sunpump sell`
  need `TRON_PRIVATE_KEY`, `TRON_MNEMONIC`, or `AGENT_WALLET_PASSWORD`.
- **Read endpoints** (`token`, `portfolio`, `tx user`, `state`,
  `quote-*`) still work without a wallet.

### Install

```bash
# 1. Install the skill (Claude Code / Cursor / Codex pick it up)
npx skills add BofAI/skills

# 2. Install / upgrade the runtime CLI
npm install -g @sun-protocol/sun-cli@^1.2.0
```

---

## Previous Releases

### v1.1.1 — 2026-05-21 _(docs only)_

- README and `SKILL.md` now document how to install the skill itself
  with `npx skills add` (vercel-labs/skills CLI), including monorepo
  `--skill` selection, branch-pinned tree-URL form for pre-merge
  installs, and the
  [vercel-labs/skills#851](https://github.com/vercel-labs/skills/issues/851)
  symlink workaround for `-g -a claude-code`.
- Pinned runtime requirement to `@sun-protocol/sun-cli@^1.2.0`.

### v1.1.0 — 2026-05-20

**Added — pre-launch bonding-curve trading.** Filled the gap between
token creation and SunSwap migration:

- `sun sunpump state <addr>` — read on-chain state
  (`NOT_EXIST` / `TRADING` / `READY_TO_LAUNCH` / `LAUNCHED`).
- `sun sunpump quote-buy <addr> --trx <decimal>` — preview buy
  (no wallet).
- `sun sunpump quote-sell <addr> --amount <decimal> [--decimals 18]` —
  preview sell (no wallet).
- `sun sunpump buy <addr> --trx <decimal> [--slippage 0.05] [--min-out <raw>]`.
- `sun sunpump sell <addr> --amount <decimal> [--decimals 18] [--slippage 0.05] [--min-out <raw>]`.

**Changed**

- Quick-start lists 7 flows (was 6); buy/sell split into post-launch
  (`sun swap`) vs pre-launch (`sun sunpump buy/sell`) paths.
- Agent Pre-Validation Checklist adds a Step 0 — `sunpump state` first —
  to pick the right trade path.
- Decimal inputs: `--trx <amount>` and `--amount <amount>` accept
  human-readable values (e.g. `10`, `1.5`). The CLI scales by TRX→Sun
  (×1e6) and token decimals before calling the contract.
- Default slippage on the bonding-curve path is `0.05` (5%) — meme
  tokens are volatile; the SDK default matches.

**Notes**

- `sun-kit`'s exported `SunPumpTokenState` enum lists only 0–2, but the
  on-chain contract returns `3` for tokens fully launched on SunSwap.
  The CLI re-labels `3 → LAUNCHED`; trust the printed label, not the
  raw int.
- First sell of a given token triggers an automatic TRC20
  `approve(MaxUint256)` tx — only the final sell tx hash is returned.

### v1.0.0 — 2026-05-20 _(initial release)_

Six core SunPump flows via `@sun-protocol/sun-cli`:

1. Buy and sell tokens through SunSwap — `sun swap` / `sun swap:quote`.
2. User position check — `sun sunpump portfolio <walletAddress>`.
3. Trade history — `sun sunpump tx user <walletAddress> --size 20`.
4. Token info — `sun sunpump token get <contractAddress>`.
5. Token ranking — `sun sunpump token ranking --type MARKET_CAP|VOLUME_24H|PRICE_CHANGE_24H --size 10`.
6. Top holders — `sun sunpump token holders <contractAddress> --size 20`.

---

**Maintainer:** Bank of AI Team
**License:** MIT — see [LICENSE](../LICENSE)
