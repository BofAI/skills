# Changelog

All notable changes to the SunPump skill will be documented in this file.

## [1.1.1] - 2026-05-21

### Docs

- README and SKILL.md now document how to install the skill itself with
  `npx skills add` (vercel-labs/skills CLI), including monorepo `--skill` selection,
  branch-pinned tree-URL form for pre-merge installs, and the
  [vercel-labs/skills#851](https://github.com/vercel-labs/skills/issues/851)
  symlink workaround for `-g -a claude-code`.
- Pinned the runtime CLI requirement to `@bankofai/sun-cli@^1.2.0`.

## [1.1.0] - 2026-05-20

### Added

- **Pre-launch trading via the SunPump bonding curve.** New commands cover the gap
  between token creation and SunSwap migration:
  - `sun sunpump state <addr>` — read on-chain state (`NOT_EXIST`/`TRADING`/`READY_TO_LAUNCH`/`LAUNCHED`)
  - `sun sunpump quote-buy  <addr> --trx <decimal>` — preview buy, no wallet
  - `sun sunpump quote-sell <addr> --amount <decimal> [--decimals 18]` — preview sell, no wallet
  - `sun sunpump buy  <addr> --trx <decimal>  [--slippage 0.05] [--min-out <raw>]`
  - `sun sunpump sell <addr> --amount <decimal> [--decimals 18] [--slippage 0.05] [--min-out <raw>]`

### Changed

- "Quick Start" lists 7 flows (was 6); buy/sell split into post-launch (`sun swap`)
  vs pre-launch (`sun sunpump buy/sell`) paths.
- "Agent Pre-Validation Checklist" adds a Step 0 — `sunpump state` first — to pick
  the right trade path. Per-path checks documented separately.
- Workflow Patterns 1 and 2 now branch by token state.
- Decimal inputs: `--trx <amount>` and `--amount <amount>` accept human-readable
  values (e.g. `10`, `1.5`). CLI scales by TRX→Sun (×1e6) and token decimals
  before calling the contract.
- Default slippage on the bonding-curve path is `0.05` (5%) — meme tokens are
  volatile; the SDK default matches.

### Notes

- `sun-kit`'s exported `SunPumpTokenState` enum lists only 0–2, but the on-chain
  contract returns `3` for tokens fully launched on SunSwap. The CLI re-labels
  `3 → LAUNCHED`; trust the printed label, not the raw int.
- First sell of a given token triggers an automatic TRC20 `approve(MaxUint256)`
  tx — only the final sell tx hash is returned.
- Requires `@bankofai/sun-cli ≥ 1.2.0`.

## [1.0.0] - 2026-05-20

### Added

Initial release. Covers six core SunPump flows via `@bankofai/sun-cli`:

1. **Buy and sell tokens** through SunSwap — `sun swap` / `sun swap:quote`
2. **User position check** — `sun sunpump portfolio <walletAddress>`
3. **Trade history** — `sun sunpump tx user <walletAddress> --size 20`
4. **Token info** — `sun sunpump token get <contractAddress>`
5. **Token ranking** — `sun sunpump token ranking --type MARKET_CAP|VOLUME_24H|PRICE_CHANGE_24H --size 10`
6. **Top holders** — `sun sunpump token holders <contractAddress> --size 20`

### Notes

- Read endpoints (2–6) require no wallet; only `sun swap` (feature 1) needs `TRON_PRIVATE_KEY` / `TRON_MNEMONIC` / `AGENT_WALLET_PASSWORD`.
- SunPump API is available on `mainnet` and `nile` only. The `shasta` network is unsupported.
- Pre-launch bonding-curve tokens (with `tokenLaunchedInstant == null`) cannot be traded through `sun swap` — verify the token is launched before quoting.
- `tx user` time filters (`--start-time` / `--end-time`) are in epoch **seconds**.
- `token ranking --type` must be exactly one of `MARKET_CAP`, `VOLUME_24H`, `PRICE_CHANGE_24H`.

---

**Maintainer**: Bank of AI Team
