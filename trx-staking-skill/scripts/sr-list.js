#!/usr/bin/env node

/**
 * sr-list.js — List Super Representatives with vote counts.
 *
 * Usage:
 *   node sr-list.js [--top <N>]     # default: top 27 (active SRs)
 */

const { getTronWeb, outputJSON, log } = require("./utils");

async function main() {
  const tronWeb = getTronWeb();
  const args = process.argv.slice(2);
  const topIdx = args.indexOf("--top");
  const topN = topIdx !== -1 ? parseInt(args[topIdx + 1], 10) : 27;

  log(`Fetching Super Representatives ...`);

  const witnesses = await tronWeb.trx.listSuperRepresentatives();
  const sorted = witnesses
    .sort((a, b) => (b.voteCount || 0) - (a.voteCount || 0))
    .slice(0, topN);

  const totalVotes = witnesses.reduce((s, w) => s + (w.voteCount || 0), 0);

  const results = sorted.map((w, i) => ({
    rank: i + 1,
    address: tronWeb.address.fromHex(w.address),
    url: w.url || "",
    vote_count: w.voteCount || 0,
    vote_share: totalVotes > 0 ? ((w.voteCount || 0) / totalVotes * 100).toFixed(2) + "%" : "0%",
    is_active_sr: i < 27,
    latest_block_num: w.latestBlockNum || 0,
  }));

  outputJSON({
    total_witnesses: witnesses.length,
    total_votes: totalVotes,
    showing: topN,
    super_representatives: results,
  });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
