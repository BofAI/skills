#!/usr/bin/env node

/**
 * vote.js — Vote for Super Representatives.
 *
 * Usage:
 *   node vote.js <srAddress> [--dry-run]                     # All votes to one SR
 *   node vote.js --split <sr1:pct,sr2:pct,...> [--dry-run]    # Split votes
 *
 * Examples:
 *   node vote.js TSR1Address --dry-run
 *   node vote.js --split TSR1:60,TSR2:40
 */

const { getTronWeb, fromSun, outputJSON, log } = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) { console.error("Usage: node vote.js <srAddress> [--dry-run] OR --split <sr1:pct,...> [--dry-run]"); process.exit(1); }

  const tronWeb = getTronWeb();
  const dryRun = args.includes("--dry-run");
  const address = tronWeb.defaultAddress.base58;
  const isSplit = args[0] === "--split";

  // Get TRON Power
  const account = await tronWeb.trx.getAccount(address);
  const frozenV2 = account.frozenV2 || [];
  const totalFrozen = frozenV2.reduce((sum, f) => sum + (f.amount || 0), 0);
  const tronPower = Math.floor(totalFrozen / 1_000_000);

  if (tronPower === 0) {
    outputJSON({ error: "No TRON Power. Stake TRX first using the energy-bandwidth skill." });
    process.exit(1);
  }

  let votes = {};

  if (isSplit) {
    const pairs = args[1].split(",");
    let totalPct = 0;
    for (const pair of pairs) {
      const [sr, pct] = pair.split(":");
      const pctNum = parseFloat(pct);
      totalPct += pctNum;
      votes[sr.trim()] = Math.floor(tronPower * pctNum / 100);
    }
    if (Math.abs(totalPct - 100) > 1) {
      log(`Warning: percentages sum to ${totalPct}%, not 100%`);
    }
  } else {
    votes[args[0]] = tronPower;
  }

  const result = {
    action: "vote",
    tron_power: tronPower,
    votes: Object.entries(votes).map(([sr, count]) => ({ sr_address: sr, vote_count: count })),
    dry_run: dryRun,
  };

  log(`Casting ${tronPower} votes ...`);

  if (dryRun) { result.status = "dry_run"; outputJSON(result); return; }

  try {
    const tx = await tronWeb.transactionBuilder.voteWitnessAccount(address, votes);
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
