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
 *   TRON_PRIVATE_KEY   — wallet private key (required by TronWeb)
 *   TRON_NETWORK       — mainnet (default) | nile
 *   TRONGRID_API_KEY   — optional TronGrid API key
 */

const {
  CONTRACTS,
  TOKEN_DECIMALS,
  TRX_DECIMALS,
  getTronWeb,
  getLauncherAddress,
  toSun,
  fromSun,
  outputJSON,
  log,
} = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error(
      "Usage: node price.js <tokenAddress> [--buy <trxAmount>] [--sell <tokenAmount>]"
    );
    process.exit(1);
  }

  const tokenAddress = args[0];
  const tronWeb = getTronWeb();
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

  const stateLabels = { 0: "active (bonding curve)", 1: "migrated (SunSwap)" };
  const result = {
    token: tokenAddress,
    price_raw: String(price),
    price_trx: fromSun(price, TRX_DECIMALS),
    state: Number(state),
    state_label: stateLabels[Number(state)] || `unknown (${state})`,
  };

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
