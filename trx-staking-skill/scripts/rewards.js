#!/usr/bin/env node

/**
 * rewards.js — Check and claim voting rewards.
 *
 * Usage:
 *   node rewards.js                    # Check pending rewards
 *   node rewards.js --claim [--dry-run] # Claim rewards
 */

const { getTronWeb, fromSun, outputJSON, log } = require("./utils");

async function main() {
  const tronWeb = getTronWeb();
  const args = process.argv.slice(2);
  const isClaim = args.includes("--claim");
  const dryRun = args.includes("--dry-run");
  const address = tronWeb.defaultAddress.base58;

  const reward = await tronWeb.trx.getReward(address).catch(() => 0);

  if (!isClaim) {
    outputJSON({
      wallet: address,
      pending_reward_trx: fromSun(reward),
      pending_reward_raw: String(reward),
      claimable: reward > 0,
    });
    return;
  }

  if (reward === 0) {
    outputJSON({ error: "No rewards to claim." });
    process.exit(1);
  }

  const result = {
    action: "claim_rewards",
    amount_trx: fromSun(reward),
    dry_run: dryRun,
  };

  log(`Claiming ${fromSun(reward)} TRX in voting rewards ...`);

  if (dryRun) { result.status = "dry_run"; outputJSON(result); return; }

  try {
    const tx = await tronWeb.transactionBuilder.withdrawBalance(address);
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
