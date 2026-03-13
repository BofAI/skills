#!/usr/bin/env node

/**
 * supply.js — Supply assets to JustLend to earn interest.
 *
 * Usage:
 *   node supply.js <asset> <amount> [--dry-run]
 *   node supply.js TRX 100 --dry-run
 *   node supply.js USDT 50
 */

const { CONTRACTS, getTronWeb, getComptroller, resolveMarket, toSun, fromSun, outputJSON, log } = require("./utils");

const MAX_UINT256 = "115792089237316195423570985008687907853269984665640564039457584007913129639935";

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) { console.error("Usage: node supply.js <asset> <amount> [--dry-run] [--no-collateral]"); process.exit(1); }

  const tronWeb = getTronWeb();
  const market = resolveMarket(args[0]);
  const amountHuman = args[1];
  const dryRun = args.includes("--dry-run");
  const noCollateral = args.includes("--no-collateral");
  const amountRaw = String(toSun(amountHuman, market.decimals));

  const result = { action: "supply", asset: market.symbol, amount: amountHuman, amount_raw: amountRaw, jToken: market.jToken, dry_run: dryRun };
  log(`Supplying ${amountHuman} ${market.symbol} to JustLend ...`);

  if (dryRun) { result.status = "dry_run"; outputJSON(result); return; }

  try {
    if (market.is_native) {
      // TRX: use payable mint()
      const jContract = await tronWeb.contract([CONTRACTS.abi.jToken.mintNative], market.jToken);
      const tx = await jContract.mint().send({ callValue: Number(amountRaw), feeLimit: 150_000_000, shouldPollResponse: false });
      result.status = "submitted";
      result.tx_id = tx;
    } else {
      // TRC20: approve then mint(amount)
      const underlying = await tronWeb.contract([CONTRACTS.abi.trc20.approve, CONTRACTS.abi.trc20.allowance], market.underlying);
      const allowance = await underlying.allowance(tronWeb.defaultAddress.base58, market.jToken).call();
      if (BigInt(allowance) < BigInt(amountRaw)) {
        log("Approving jToken to spend underlying ...");
        await underlying.approve(market.jToken, MAX_UINT256).send({ feeLimit: 50_000_000, shouldPollResponse: false });
        await new Promise((r) => setTimeout(r, 4000));
      }
      const jContract = await tronWeb.contract([CONTRACTS.abi.jToken.mint], market.jToken);
      const tx = await jContract.mint(amountRaw).send({ feeLimit: 150_000_000, shouldPollResponse: false });
      result.status = "submitted";
      result.tx_id = tx;
    }
    log(`Transaction: ${result.tx_id}`);

    // Enable as collateral by default (needed for borrowing against this asset)
    if (!noCollateral) {
      log("Entering market to enable as collateral ...");
      await new Promise((r) => setTimeout(r, 3000));
      const comptrollerAddr = getComptroller();
      const comptroller = await tronWeb.contract([CONTRACTS.abi.comptroller.enterMarkets], comptrollerAddr);
      const enterTx = await comptroller.enterMarkets([market.jToken]).send({ feeLimit: 100_000_000, shouldPollResponse: false });
      result.collateral_enabled = true;
      result.enter_markets_tx = enterTx;
      log(`Collateral enabled: ${enterTx}`);
    }
  } catch (e) {
    result.status = "failed";
    result.error = e.message || String(e);
  }

  outputJSON(result);
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
