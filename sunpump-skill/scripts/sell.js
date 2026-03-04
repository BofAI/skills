#!/usr/bin/env node

/**
 * sell.js — Sell SunPump tokens back for TRX via the bonding curve.
 *
 * Usage:
 *   node sell.js <tokenAddress> <tokenAmount> [--slippage <percent>] [--dry-run]
 *   node sell.js <tokenAddress> all [--slippage <percent>] [--dry-run]
 *
 * Arguments:
 *   tokenAddress   — TRC20 address of the SunPump token
 *   tokenAmount    — amount of tokens to sell (human-readable) or "all"
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
  TOKEN_DECIMALS,
  TRX_DECIMALS,
  MAX_UINT256,
  getTronWeb,
  getLauncherAddress,
  toSun,
  fromSun,
  applySlippage,
  outputJSON,
  log,
} = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error(
      "Usage: node sell.js <tokenAddress> <tokenAmount|all> [--slippage <pct>] [--dry-run]"
    );
    process.exit(1);
  }

  const tokenAddress = args[0];
  const tokenAmountArg = args[1];
  const slippageIdx = args.indexOf("--slippage");
  const slippage =
    slippageIdx !== -1 ? parseFloat(args[slippageIdx + 1]) : 5;
  const dryRun = args.includes("--dry-run");

  const tronWeb = getTronWeb();
  const launcherAddr = getLauncherAddress();
  const walletAddress = tronWeb.defaultAddress.base58;

  log(`Preparing to sell token ${tokenAddress} ...`);

  // Step 1: Check token state
  const launcher = await tronWeb.contract(
    [
      CONTRACTS.abi.getTokenState,
      CONTRACTS.abi.getTrxAmountBySaleWithFee,
      CONTRACTS.abi.saleToken,
    ],
    launcherAddr
  );

  const state = await launcher.getTokenState(tokenAddress).call();
  if (Number(state) !== 0) {
    outputJSON({
      error: "Token has migrated to SunSwap. Use SunSwap skill to trade.",
      state: Number(state),
    });
    process.exit(1);
  }

  // Step 2: Determine token amount
  const tokenContract = await tronWeb.contract(
    [CONTRACTS.abi.balanceOf, CONTRACTS.abi.allowance, CONTRACTS.abi.approve],
    tokenAddress
  );

  let tokenAmountRaw;
  if (tokenAmountArg.toLowerCase() === "all") {
    tokenAmountRaw = String(await tokenContract.balanceOf(walletAddress).call());
    if (tokenAmountRaw === "0") {
      outputJSON({ error: "Token balance is zero. Nothing to sell." });
      process.exit(1);
    }
    log(`Selling full balance: ${fromSun(tokenAmountRaw, TOKEN_DECIMALS)} tokens`);
  } else {
    tokenAmountRaw = String(toSun(tokenAmountArg, TOKEN_DECIMALS));
  }

  // Step 3: Get sale estimate
  const est = await launcher
    .getTrxAmountBySaleWithFee(tokenAddress, tokenAmountRaw)
    .call();

  const expectedTrx = String(est.trxAmount);
  const minTrx = String(applySlippage(expectedTrx, slippage));

  const result = {
    action: "sell",
    token: tokenAddress,
    token_amount:
      tokenAmountArg.toLowerCase() === "all"
        ? fromSun(tokenAmountRaw, TOKEN_DECIMALS)
        : tokenAmountArg,
    token_amount_raw: tokenAmountRaw,
    expected_trx: fromSun(expectedTrx, TRX_DECIMALS),
    expected_trx_raw: expectedTrx,
    min_trx_with_slippage: fromSun(minTrx, TRX_DECIMALS),
    min_trx_raw: minTrx,
    fee_trx: fromSun(est.fee, TRX_DECIMALS),
    slippage_percent: slippage,
    dry_run: dryRun,
  };

  log(
    `Estimate: ${result.expected_trx} TRX (min: ${result.min_trx_with_slippage} with ${slippage}% slippage)`
  );
  log(`Fee: ${result.fee_trx} TRX`);

  if (dryRun) {
    result.status = "dry_run";
    log("Dry run — no transaction sent.");
    outputJSON(result);
    return;
  }

  // Step 4: Check and set allowance
  const currentAllowance = await tokenContract
    .allowance(walletAddress, launcherAddr)
    .call();

  if (BigInt(currentAllowance) < BigInt(tokenAmountRaw)) {
    log("Approving SunPump to spend tokens ...");
    try {
      const approveTx = await tokenContract
        .approve(launcherAddr, MAX_UINT256)
        .send({ feeLimit: 50_000_000, shouldPollResponse: false });
      result.approve_tx = approveTx;
      log(`Approval submitted: ${approveTx}`);
      // Wait for approval to propagate
      log("Waiting for approval confirmation ...");
      await new Promise((r) => setTimeout(r, 4000));
    } catch (err) {
      result.status = "approval_failed";
      result.error = err.message || String(err);
      log(`Approval failed: ${result.error}`);
      outputJSON(result);
      return;
    }
  } else {
    log("Allowance already sufficient.");
  }

  // Step 5: Execute sale
  log("Sending saleToken transaction ...");
  try {
    const tx = await launcher
      .saleToken(tokenAddress, tokenAmountRaw, minTrx)
      .send({ feeLimit: 150_000_000, shouldPollResponse: false });

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
