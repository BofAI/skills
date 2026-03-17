#!/usr/bin/env node

/**
 * withdraw.js — Withdraw supplied assets from JustLend.
 *
 * Usage:
 *   node withdraw.js <asset> <amount|all> [--dry-run]
 */

const { CONTRACTS, getTronWeb, resolveMarket, toSun, fromSun, outputJSON, log } = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) { console.error("Usage: node withdraw.js <asset> <amount|all> [--dry-run]"); process.exit(1); }

  const tronWeb = getTronWeb();
  const market = resolveMarket(args[0]);
  const amountArg = args[1];
  const dryRun = args.includes("--dry-run");
  const walletAddress = tronWeb.defaultAddress.base58;

  const jContract = await tronWeb.contract(
    [CONTRACTS.abi.jToken.balanceOf, CONTRACTS.abi.jToken.redeem, CONTRACTS.abi.jToken.redeemUnderlying],
    market.jToken
  );

  const result = { action: "withdraw", asset: market.symbol, jToken: market.jToken, dry_run: dryRun };

  if (amountArg.toLowerCase() === "all") {
    const jBalance = await jContract.balanceOf(walletAddress).call();
    if (Number(jBalance) === 0) { outputJSON({ error: "No jTokens to redeem." }); process.exit(1); }
    result.jToken_balance = fromSun(jBalance, market.jDecimals);
    result.redeem_method = "redeem (all jTokens)";
    log(`Withdrawing all jTokens (${result.jToken_balance}) ...`);
    if (dryRun) { result.status = "dry_run"; outputJSON(result); return; }
    try {
      const tx = await jContract.redeem(String(jBalance)).send({ feeLimit: 150_000_000, shouldPollResponse: false });
      result.status = "submitted"; result.tx_id = tx;
    } catch (e) { result.status = "failed"; result.error = e.message || String(e); }
  } else {
    const amountRaw = String(toSun(amountArg, market.decimals));
    result.amount = amountArg;
    result.amount_raw = amountRaw;
    result.redeem_method = "redeemUnderlying (exact amount)";
    log(`Withdrawing ${amountArg} ${market.symbol} ...`);
    if (dryRun) { result.status = "dry_run"; outputJSON(result); return; }
    try {
      const tx = await jContract.redeemUnderlying(amountRaw).send({ feeLimit: 150_000_000, shouldPollResponse: false });
      result.status = "submitted"; result.tx_id = tx;
    } catch (e) { result.status = "failed"; result.error = e.message || String(e); }
  }

  outputJSON(result);
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
