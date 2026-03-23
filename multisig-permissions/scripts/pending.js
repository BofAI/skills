#!/usr/bin/env node

/**
 * pending.js — List pending multi-sig proposals.
 *
 * Usage:
 *   node pending.js [--status awaiting|ready|expired|all]
 *
 * Examples:
 *   node pending.js
 *   node pending.js --status ready
 *   node pending.js --status all
 */

const { listProposals, outputJSON, log } = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  let statusFilter = "all";

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--status" && args[i + 1]) { statusFilter = args[++i].toLowerCase(); }
  }

  log("Loading pending proposals ...");
  const proposals = listProposals();

  if (proposals.length === 0) {
    outputJSON({
      pending: [],
      summary: { awaiting: 0, ready: 0, expired: 0, total: 0 },
      message: "No pending proposals. Create one with: node propose.js transfer <to> <amount>",
    });
    return;
  }

  const now = new Date();
  const enriched = proposals.map(p => {
    const collectedWeight = p.signers.reduce((s, k) => s + k.weight, 0);
    const thresholdMet = collectedWeight >= p.threshold;
    const isExpired = new Date(p.expiresAt) < now;

    let status;
    if (isExpired) status = "expired";
    else if (thresholdMet) status = "ready";
    else status = "awaiting";

    const remainingWeight = Math.max(0, p.threshold - collectedWeight);
    const timeRemaining = isExpired ? "expired" : formatTimeRemaining(new Date(p.expiresAt) - now);

    return {
      proposalId: p.proposalId,
      description: p.description,
      memo: p.memo || "",
      permission: p.permission,
      created: p.createdAt,
      expires: p.expiresAt,
      time_remaining: timeRemaining,
      signatures: `${p.signaturesCollected}/${p.threshold}`,
      collected_weight: collectedWeight,
      required_weight: p.threshold,
      status,
      signers: p.signers.map(s => s.address),
      remaining_weight: remainingWeight,
    };
  });

  // Apply filter
  const filtered = statusFilter === "all" ? enriched : enriched.filter(p => p.status === statusFilter);

  // Compute summary
  const summary = {
    awaiting: enriched.filter(p => p.status === "awaiting").length,
    ready: enriched.filter(p => p.status === "ready").length,
    expired: enriched.filter(p => p.status === "expired").length,
    total: enriched.length,
  };

  outputJSON({
    filter: statusFilter,
    pending: filtered,
    summary,
  });
}

function formatTimeRemaining(ms) {
  if (ms <= 0) return "expired";
  const hours = Math.floor(ms / (1000 * 60 * 60));
  const minutes = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));
  if (hours > 24) return `${Math.floor(hours / 24)}d ${hours % 24}h`;
  return `${hours}h ${minutes}m`;
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
