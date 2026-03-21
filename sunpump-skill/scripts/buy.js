#!/usr/bin/env node

/**
 * buy.js — Purchase tokens on SunPump bonding curve.
 *
 * Usage:
 *   node buy.js <tokenAddress> <trxAmount> [--slippage <percent>] [--dry-run]
 *
 * Arguments:
 *   tokenAddress   — TRC20 address of the SunPump token
 *   trxAmount      — amount of TRX to spend (human-readable, e.g. "100")
 *   --slippage     — slippage tolerance in percent (default: 5)
 *   --dry-run      — only estimate, do not execute
 *
 * Environment:
 *   TRON_PRIVATE_KEY   — wallet private key (required)
 *   TRON_NETWORK       — mainnet (default) | nile
 *   TRONGRID_API_KEY   — optional TronGrid API key
 */

const {
  CONTRACTS,
  SLIPPAGE,
  TOKEN_DECIMALS,
  TRX_DECIMALS,
  getTronWeb,
  getLauncherAddress,
  toSun,
  fromSun,
  validateSlippage,
  applySlippage,
  outputJSON,
  log,
} = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error(
      "Usage: node buy.js <tokenAddress> <trxAmount> [--slippage <pct>] [--dry-run]"
    );
    process.exit(1);
  }

  const tokenAddress = args[0];
  const trxAmountHuman = args[1];
  const slippageIdx = args.indexOf("--slippage");
  const slippageArg = slippageIdx !== -1 ? parseFloat(args[slippageIdx + 1]) : undefined;
  const slippage = validateSlippage(slippageArg);
  const dryRun = args.includes("--dry-run");

  const tronWeb = getTronWeb();
  const launcherAddr = getLauncherAddress();
  const trxAmountSun = toSun(trxAmountHuman, TRX_DECIMALS);

  log(`Preparing to buy token ${tokenAddress} with ${trxAmountHuman} TRX ...`);

  // Step 1: Check token state
  const launcher = await tronWeb.contract(
    [
      CONTRACTS.abi.getTokenState,
      CONTRACTS.abi.getTokenAmountByPurchaseWithFee,
      CONTRACTS.abi.purchaseToken,
    ],
    launcherAddr
  );

  const state = await launcher.getTokenState(tokenAddress).call();
  const stateNum = Number(state);
  if (stateNum !== 1) {
    const sunswapRouter = CONTRACTS.networks[(process.env.TRON_NETWORK || "mainnet").toLowerCase()].sunswap_v2_router;
    const stateLabels = { 0: "not registered", 2: "pending migration", 3: "migrated (SunSwap V2)" };
    const label = stateLabels[stateNum] || `unknown (${stateNum})`;
    outputJSON({
      error: stateNum === 3
        ? "Token has migrated to SunSwap V2. The bonding curve is closed."
        : `Token is not active on the bonding curve (state: ${label}).`,
      state: stateNum,
      state_label: label,
      ...(stateNum === 3 && {
        migration: {
          reason: "Token reached the ~$69,420 market cap threshold and liquidity was moved to SunSwap V2.",
          sunswap_router: sunswapRouter ? sunswapRouter.address : null,
          action: "Use the SunSwap skill to trade this token. The SunPump bonding-curve scripts will not work for migrated tokens.",
        },
      }),
    });
    process.exit(1);
  }

  // Step 2: Get estimate
  const est = await launcher
    .getTokenAmountByPurchaseWithFee(tokenAddress, String(trxAmountSun))
    .call();

  const expectedTokens = String(est.tokenAmount);
  const minTokens = String(applySlippage(expectedTokens, slippage));

  const result = {
    action: "buy",
    token: tokenAddress,
    trx_amount: trxAmountHuman,
    trx_amount_raw: String(trxAmountSun),
    expected_tokens: fromSun(expectedTokens, TOKEN_DECIMALS),
    expected_tokens_raw: expectedTokens,
    min_tokens_with_slippage: fromSun(minTokens, TOKEN_DECIMALS),
    min_tokens_raw: minTokens,
    fee_trx: fromSun(est.fee, TRX_DECIMALS),
    slippage_percent: slippage,
    dry_run: dryRun,
  };

  log(
    `Estimate: ${result.expected_tokens} tokens (min: ${result.min_tokens_with_slippage} with ${slippage}% slippage)`
  );
  log(`Fee: ${result.fee_trx} TRX`);

  if (dryRun) {
    result.status = "dry_run";
    log("Dry run — no transaction sent.");
    outputJSON(result);
    return;
  }

  // Step 3: Execute purchase
  log("Sending purchaseToken transaction ...");
  try {
    const tx = await launcher
      .purchaseToken(tokenAddress, minTokens)
      .send({
        callValue: Number(trxAmountSun),
        feeLimit: 150_000_000,
        shouldPollResponse: false,
      });

    result.status = "submitted";
    result.tx_id = tx;
    log(`Transaction submitted: ${tx}`);
  } catch (err) {
    result.status = "failed";
    result.error = err.message || String(err);
    log(`Transaction failed: ${result.error}`);
  }

  outputJSON(result);
}

main().catch((err) => {
  outputJSON({ error: err.message });
  process.exit(1);
});
