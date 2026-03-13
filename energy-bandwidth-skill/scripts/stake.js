#!/usr/bin/env node

/**
 * stake.js — Stake TRX for Energy or Bandwidth (Freeze Balance V2).
 *
 * Usage:
 *   node stake.js <amount> <ENERGY|BANDWIDTH> [--dry-run]
 */

const { getTronWeb, toSun, fromSun, outputJSON, log } = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) { console.error("Usage: node stake.js <amount> <ENERGY|BANDWIDTH> [--dry-run]"); process.exit(1); }

  const tronWeb = getTronWeb();
  const amountTrx = args[0];
  const resource = args[1].toUpperCase();
  const dryRun = args.includes("--dry-run");

  if (!["ENERGY", "BANDWIDTH"].includes(resource)) {
    outputJSON({ error: "Resource must be ENERGY or BANDWIDTH" });
    process.exit(1);
  }

  const amountSun = Number(toSun(amountTrx));
  const balance = await tronWeb.trx.getBalance(tronWeb.defaultAddress.base58);

  if (amountSun > balance) {
    outputJSON({ error: `Insufficient TRX. Have ${fromSun(balance)}, need ${amountTrx}` });
    process.exit(1);
  }

  const result = {
    action: "stake",
    amount_trx: amountTrx,
    resource,
    dry_run: dryRun,
  };

  log(`Staking ${amountTrx} TRX for ${resource} ...`);

  if (dryRun) { result.status = "dry_run"; outputJSON(result); return; }

  try {
    const tx = await tronWeb.transactionBuilder.freezeBalanceV2(amountSun, resource);
    const signed = await tronWeb.trx.sign(tx);
    const broadcast = await tronWeb.trx.sendRawTransaction(signed);
    result.status = broadcast.result ? "submitted" : "failed";
    result.tx_id = broadcast.txid;
    log(`Transaction: ${broadcast.txid}`);
  } catch (e) {
    result.status = "failed";
    result.error = e.message || String(e);
  }

  outputJSON(result);
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
