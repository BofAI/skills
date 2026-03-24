#!/usr/bin/env node

/**
 * unstake.js — Begin TRX unstake (14-day cooldown) or withdraw expired unstakes.
 *
 * Usage:
 *   node unstake.js <amount> <ENERGY|BANDWIDTH> [--dry-run]    # Begin cooldown
 *   node unstake.js --withdraw [--dry-run]                      # Claim expired
 */

const { getTronWeb, toSun, outputJSON, log } = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  const tronWeb = getTronWeb();
  const dryRun = args.includes("--dry-run");
  const isWithdraw = args.includes("--withdraw");

  if (isWithdraw) {
    log("Withdrawing expired unstakes ...");
    const result = { action: "withdraw_unstake", dry_run: dryRun };

    if (dryRun) { result.status = "dry_run"; outputJSON(result); return; }

    try {
      const tx = await tronWeb.transactionBuilder.withdrawExpireUnfreeze();
      const signed = await tronWeb.trx.sign(tx);
      const broadcast = await tronWeb.trx.sendRawTransaction(signed);
      result.status = broadcast.result ? "submitted" : "failed";
      result.tx_id = broadcast.txid;
    } catch (e) {
      result.status = "failed";
      result.error = e.message || String(e);
    }
    outputJSON(result);
    return;
  }

  if (args.length < 2) {
    console.error("Usage: node unstake.js <amount> <ENERGY|BANDWIDTH> [--dry-run]  OR  --withdraw [--dry-run]");
    process.exit(1);
  }

  const amountTrx = args[0];
  const resource = args[1].toUpperCase();
  const amountSun = Number(toSun(amountTrx));

  if (!["ENERGY", "BANDWIDTH"].includes(resource)) {
    outputJSON({ error: "Resource must be ENERGY or BANDWIDTH" });
    process.exit(1);
  }

  const result = { action: "begin_unstake", amount_trx: amountTrx, resource, cooldown_days: 14, dry_run: dryRun };
  log(`Beginning unstake of ${amountTrx} TRX from ${resource} (14-day cooldown) ...`);

  if (dryRun) { result.status = "dry_run"; outputJSON(result); return; }

  try {
    const tx = await tronWeb.transactionBuilder.unfreezeBalanceV2(amountSun, resource);
    const signed = await tronWeb.trx.sign(tx);
    const broadcast = await tronWeb.trx.sendRawTransaction(signed);
    result.status = broadcast.result ? "submitted" : "failed";
    result.tx_id = broadcast.txid;
  } catch (e) {
    result.status = "failed";
    result.error = e.message || String(e);
  }

  outputJSON(result);
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
