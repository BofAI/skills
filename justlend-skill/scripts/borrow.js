#!/usr/bin/env node

/**
 * borrow.js — Borrow assets against JustLend collateral.
 *
 * Usage:
 *   node borrow.js <asset> <amount> [--dry-run]
 */

const { CONTRACTS, getTronWeb, resolveMarket, getComptroller, toSun, outputJSON, log } = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) { console.error("Usage: node borrow.js <asset> <amount> [--collateral <SYMBOL>] [--dry-run]"); process.exit(1); }

  const tronWeb = getTronWeb();
  const market = resolveMarket(args[0]);
  const amountHuman = args[1];
  const dryRun = args.includes("--dry-run");
  const amountRaw = String(toSun(amountHuman, market.decimals));

  // Optional: enter a collateral market before borrowing
  const collateralIdx = args.indexOf("--collateral");
  const collateralSymbol = collateralIdx !== -1 ? args[collateralIdx + 1] : null;

  const result = { action: "borrow", asset: market.symbol, amount: amountHuman, amount_raw: amountRaw, dry_run: dryRun };
  log(`Borrowing ${amountHuman} ${market.symbol} from JustLend ...`);

  if (dryRun) { result.status = "dry_run"; outputJSON(result); return; }

  try {
    // Enter collateral market if specified (enables that asset as collateral)
    if (collateralSymbol) {
      const collateralMarket = resolveMarket(collateralSymbol);
      const comptrollerAddr = getComptroller();
      const comptroller = await tronWeb.contract([CONTRACTS.abi.comptroller.enterMarkets], comptrollerAddr);
      log(`Entering ${collateralSymbol} market as collateral ...`);
      await comptroller.enterMarkets([collateralMarket.jToken]).send({ feeLimit: 100_000_000, shouldPollResponse: false });
      result.collateral_market = collateralSymbol;
      await new Promise((r) => setTimeout(r, 3000));
    }

    const jContract = await tronWeb.contract([CONTRACTS.abi.jToken.borrow], market.jToken);
    const tx = await jContract.borrow(amountRaw).send({ feeLimit: 150_000_000, shouldPollResponse: false });
    result.status = "submitted";
    result.tx_id = tx;
    log(`Transaction: ${tx}`);
  } catch (e) {
    result.status = "failed";
    result.error = e.message || String(e);
  }

  outputJSON(result);
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
