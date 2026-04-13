#!/usr/bin/env node

/**
 * repay.js — Repay borrowed assets on JustLend.
 *
 * Usage:
 *   node repay.js <asset> <amount|all> [--dry-run]
 */

const { CONTRACTS, getTronWeb, resolveMarket, toSun, fromSun, outputJSON, log } = require("./utils");

const MAX_UINT256 = "115792089237316195423570985008687907853269984665640564039457584007913129639935";

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) { console.error("Usage: node repay.js <asset> <amount|all> [--dry-run]"); process.exit(1); }

  const tronWeb = getTronWeb();
  const market = resolveMarket(args[0]);
  const amountArg = args[1];
  const dryRun = args.includes("--dry-run");
  const walletAddress = tronWeb.defaultAddress.base58;

  // Use max uint256 for "all" to repay full borrow
  const amountRaw = amountArg.toLowerCase() === "all" ? MAX_UINT256 : String(toSun(amountArg, market.decimals));

  const result = { action: "repay", asset: market.symbol, amount: amountArg, dry_run: dryRun };
  log(`Repaying ${amountArg} ${market.symbol} on JustLend ...`);

  if (dryRun) { result.status = "dry_run"; outputJSON(result); return; }

  try {
    if (market.is_native) {
      // TRX: use payable repayBorrow
      const jContract = await tronWeb.contract([CONTRACTS.abi.jToken.repayBorrowNative], market.jToken);
      const tx = await jContract.repayBorrow().send({ callValue: Number(amountRaw === MAX_UINT256 ? 0 : amountRaw), feeLimit: 150_000_000, shouldPollResponse: false });
      result.status = "submitted"; result.tx_id = tx;
    } else {
      // TRC20: approve then repayBorrow
      const underlying = await tronWeb.contract([CONTRACTS.abi.trc20.approve, CONTRACTS.abi.trc20.allowance], market.underlying);
      const allowance = await underlying.allowance(walletAddress, market.jToken).call();
      if (BigInt(allowance) < BigInt(amountRaw === MAX_UINT256 ? "1" : amountRaw)) {
        log("Approving jToken to spend underlying ...");
        await underlying.approve(market.jToken, MAX_UINT256).send({ feeLimit: 50_000_000, shouldPollResponse: false });
        await new Promise((r) => setTimeout(r, 4000));
      }
      const jContract = await tronWeb.contract([CONTRACTS.abi.jToken.repayBorrow], market.jToken);
      const tx = await jContract.repayBorrow(amountRaw).send({ feeLimit: 150_000_000, shouldPollResponse: false });
      result.status = "submitted"; result.tx_id = tx;
    }
    log(`Transaction: ${result.tx_id}`);
  } catch (e) {
    result.status = "failed";
    result.error = e.message || String(e);
  }

  outputJSON(result);
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
