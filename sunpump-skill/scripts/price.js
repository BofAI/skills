#!/usr/bin/env node

/**
 * price.js — Query SunPump token price, state, and trade estimates.
 *
 * Usage:
 *   node price.js <tokenAddress>                     # basic price + state
 *   node price.js <tokenAddress> --buy  <trxAmount>   # estimate buy
 *   node price.js <tokenAddress> --sell <tokenAmount>  # estimate sell
 *
 * Environment:
 *   TRON_NETWORK       — mainnet (default) | nile
 *   TRONGRID_API_KEY   — optional TronGrid API key
 */

const {
  CONTRACTS,
  TOKEN_DECIMALS,
  TRX_DECIMALS,
  getTronWebReadOnly,
  getLauncherAddress,
  toSun,
  fromSun,
  outputJSON,
  log,
} = require("./utils");

const NETWORK = (process.env.TRON_NETWORK || "mainnet").toLowerCase();

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error(
      "Usage: node price.js <tokenAddress> [--buy <trxAmount>] [--sell <tokenAmount>]"
    );
    process.exit(1);
  }

  const tokenAddress = args[0];
  const tronWeb = getTronWebReadOnly();
  const launcherAddr = getLauncherAddress();

  log(`Querying SunPump for token ${tokenAddress} ...`);

  const launcher = await tronWeb.contract(
    [
      CONTRACTS.abi.getPrice,
      CONTRACTS.abi.getTokenState,
      CONTRACTS.abi.getTokenAmountByPurchaseWithFee,
      CONTRACTS.abi.getTrxAmountBySaleWithFee,
    ],
    launcherAddr
  );

  // Basic price and state
  const [price, state] = await Promise.all([
    launcher.getPrice(tokenAddress).call(),
    launcher.getTokenState(tokenAddress).call(),
  ]);

  const stateNum = Number(state);
  const stateLabels = { 0: "not registered", 1: "active (bonding curve)", 2: "pending migration", 3: "migrated (SunSwap V2)" };
  const result = {
    token: tokenAddress,
    price_raw: String(price),
    price_trx: fromSun(price, TRX_DECIMALS),
    state: stateNum,
    state_label: stateLabels[stateNum] || `unknown (${stateNum})`,
  };

  if (stateNum === 3) {
    const sunswapRouter = CONTRACTS.networks[NETWORK].sunswap_v2_router;
    result.migration = {
      reason: "Token reached the ~$69,420 market cap threshold and liquidity was moved to SunSwap V2.",
      sunswap_router: sunswapRouter ? sunswapRouter.address : null,
      action: "Use the SunSwap skill to trade this token.",
    };
    log("WARNING: This token has migrated to SunSwap V2. Bonding-curve trading is no longer available.");
  } else if (stateNum !== 1) {
    log(`WARNING: Token state is "${stateLabels[stateNum] || stateNum}" — bonding-curve trading may not be available.`);
  }

  // Optional buy estimate
  const buyIdx = args.indexOf("--buy");
  if (buyIdx !== -1 && args[buyIdx + 1]) {
    const trxAmount = toSun(args[buyIdx + 1], TRX_DECIMALS);
    const est = await launcher
      .getTokenAmountByPurchaseWithFee(tokenAddress, String(trxAmount))
      .call();
    result.buy_estimate = {
      trx_in: args[buyIdx + 1],
      tokens_out: fromSun(est.tokenAmount, TOKEN_DECIMALS),
      tokens_out_raw: String(est.tokenAmount),
      fee_raw: String(est.fee),
      fee_trx: fromSun(est.fee, TRX_DECIMALS),
    };
    log(
      `Buy estimate: ${args[buyIdx + 1]} TRX -> ${result.buy_estimate.tokens_out} tokens (fee: ${result.buy_estimate.fee_trx} TRX)`
    );
  }

  // Optional sell estimate
  const sellIdx = args.indexOf("--sell");
  if (sellIdx !== -1 && args[sellIdx + 1]) {
    const tokenAmount = toSun(args[sellIdx + 1], TOKEN_DECIMALS);
    const est = await launcher
      .getTrxAmountBySaleWithFee(tokenAddress, String(tokenAmount))
      .call();
    result.sell_estimate = {
      tokens_in: args[sellIdx + 1],
      trx_out: fromSun(est.trxAmount, TRX_DECIMALS),
      trx_out_raw: String(est.trxAmount),
      fee_raw: String(est.fee),
      fee_trx: fromSun(est.fee, TRX_DECIMALS),
    };
    log(
      `Sell estimate: ${args[sellIdx + 1]} tokens -> ${result.sell_estimate.trx_out} TRX (fee: ${result.sell_estimate.fee_trx} TRX)`
    );
  }

  outputJSON(result);
}

main().catch((err) => {
  outputJSON({ error: err.message });
  process.exit(1);
});
