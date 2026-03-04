#!/usr/bin/env node

/**
 * delegate.js — Delegate or undelegate Energy/Bandwidth to another account.
 *
 * Usage:
 *   node delegate.js <toAddress> <amount> <ENERGY|BANDWIDTH> [--dry-run]
 *   node delegate.js --undelegate <fromAddress> <amount> <ENERGY|BANDWIDTH> [--dry-run]
 */

const { getTronWeb, toSun, outputJSON, log } = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  const tronWeb = getTronWeb();
  const dryRun = args.includes("--dry-run");
  const isUndelegate = args[0] === "--undelegate";

  if (isUndelegate) {
    if (args.length < 4) {
      console.error("Usage: node delegate.js --undelegate <fromAddress> <amount> <ENERGY|BANDWIDTH> [--dry-run]");
      process.exit(1);
    }
    const receiverAddress = args[1];
    const amountSun = Number(toSun(args[2]));
    const resource = args[3].toUpperCase();
    const result = { action: "undelegate", receiver: receiverAddress, amount_trx: args[2], resource, dry_run: dryRun };

    log(`Undelegating ${args[2]} TRX ${resource} from ${receiverAddress} ...`);
    if (dryRun) { result.status = "dry_run"; outputJSON(result); return; }

    try {
      const tx = await tronWeb.transactionBuilder.undelegateResource(amountSun, receiverAddress, resource);
      const signed = await tronWeb.trx.sign(tx);
      const broadcast = await tronWeb.trx.sendRawTransaction(signed);
      result.status = broadcast.result ? "submitted" : "failed";
      result.tx_id = broadcast.txid;
    } catch (e) { result.status = "failed"; result.error = e.message || String(e); }
    outputJSON(result);
    return;
  }

  if (args.length < 3) {
    console.error("Usage: node delegate.js <toAddress> <amount> <ENERGY|BANDWIDTH> [--dry-run]");
    process.exit(1);
  }

  const toAddress = args[0];
  const amountSun = Number(toSun(args[1]));
  const resource = args[2].toUpperCase();
  const result = { action: "delegate", to: toAddress, amount_trx: args[1], resource, dry_run: dryRun };

  log(`Delegating ${args[1]} TRX ${resource} to ${toAddress} ...`);
  if (dryRun) { result.status = "dry_run"; outputJSON(result); return; }

  try {
    const tx = await tronWeb.transactionBuilder.delegateResource(amountSun, toAddress, resource);
    const signed = await tronWeb.trx.sign(tx);
    const broadcast = await tronWeb.trx.sendRawTransaction(signed);
    result.status = broadcast.result ? "submitted" : "failed";
    result.tx_id = broadcast.txid;
  } catch (e) { result.status = "failed"; result.error = e.message || String(e); }
  outputJSON(result);
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
