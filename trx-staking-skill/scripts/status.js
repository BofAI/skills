#!/usr/bin/env node

/**
 * status.js — Staking overview: frozen TRX, TRON Power, current votes, pending rewards.
 *
 * Usage:
 *   node status.js [walletAddress]
 */

const { getTronWeb, fromSun, outputJSON, log } = require("./utils");

async function main() {
  const tronWeb = getTronWeb();
  const address = process.argv[2] || tronWeb.defaultAddress.base58;
  log(`Checking staking status for ${address} ...`);

  const [account, reward, trxBalance] = await Promise.all([
    tronWeb.trx.getAccount(address),
    tronWeb.trx.getReward(address).catch(() => 0),
    tronWeb.trx.getBalance(address),
  ]);

  const frozenV2 = account.frozenV2 || [];
  const totalFrozen = frozenV2.reduce((sum, f) => sum + (f.amount || 0), 0);

  const votes = (account.votes || []).map((v) => ({
    sr_address: tronWeb.address.fromHex(v.vote_address),
    vote_count: v.vote_count,
  }));

  const totalVotes = votes.reduce((sum, v) => sum + v.vote_count, 0);

  outputJSON({
    wallet: address,
    trx_balance: fromSun(trxBalance),
    tron_power: totalFrozen / 1_000_000,
    total_frozen_trx: fromSun(totalFrozen),
    frozen_breakdown: frozenV2.map((f) => ({
      type: f.type || "BANDWIDTH",
      amount_trx: fromSun(f.amount || 0),
    })),
    votes,
    total_votes: totalVotes,
    unused_tron_power: (totalFrozen / 1_000_000) - totalVotes,
    pending_reward_trx: fromSun(reward),
  });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
