#!/usr/bin/env node

/**
 * execute.js — Broadcast a fully-signed multi-sig transaction.
 *
 * Usage:
 *   node execute.js <proposal-id> [--dry-run]
 *
 * Examples:
 *   node execute.js prop_1709312400_a3f2 --dry-run
 *   node execute.js prop_1709312400_a3f2
 */

const {
  getTronWeb, loadProposal, archiveProposal, outputJSON, log,
} = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error("Usage: node execute.js <proposal-id> [--dry-run]");
    process.exit(1);
  }

  const proposalRef = args[0];
  const dryRun = args.includes("--dry-run");

  const tronWeb = getTronWeb();

  log(`Loading proposal "${proposalRef}" ...`);
  const proposal = loadProposal(proposalRef);

  // Display summary
  log("");
  log(`  Proposal:    ${proposal.proposalId}`);
  log(`  Description: ${proposal.description}`);
  log(`  Signatures:  ${proposal.signaturesCollected}`);
  log(`  Threshold:   ${proposal.threshold}`);
  log(`  Expires:     ${proposal.expiresAt}`);
  log("");

  // Validate threshold
  const collectedWeight = proposal.signers.reduce((s, k) => s + k.weight, 0);
  if (collectedWeight < proposal.threshold) {
    outputJSON({
      error: `Threshold not met. Have weight ${collectedWeight}, need ${proposal.threshold}`,
      proposalId: proposal.proposalId,
      signatures: proposal.signers.map(s => s.address),
    });
    process.exit(1);
  }

  // Validate not expired
  if (new Date(proposal.expiresAt) < new Date()) {
    outputJSON({
      error: "Proposal has expired",
      proposalId: proposal.proposalId,
      expiredAt: proposal.expiresAt,
    });
    process.exit(1);
  }

  const result = {
    action: "execute",
    proposalId: proposal.proposalId,
    description: proposal.description,
    signatures: proposal.signaturesCollected,
    threshold: proposal.threshold,
    dry_run: dryRun,
  };

  if (dryRun) {
    result.status = "dry_run";
    result.message = "Transaction is valid and ready to broadcast";
    result.signers = proposal.signers.map(s => s.address);
    outputJSON(result);
    return;
  }

  // Broadcast
  log("Broadcasting transaction ...");
  try {
    const broadcast = await tronWeb.trx.sendRawTransaction(proposal.transaction);
    result.status = broadcast.result ? "submitted" : "failed";
    result.tx_id = broadcast.txid;

    if (broadcast.result) {
      const archivedTo = archiveProposal(proposal.proposalId);
      result.archived_to = archivedTo;
      log(`Transaction: ${broadcast.txid}`);
      log(`Proposal archived to ${archivedTo}`);
    } else {
      result.broadcast_error = broadcast.message || broadcast.code || "Unknown error";
      log(`Broadcast failed: ${result.broadcast_error}`);
    }
  } catch (e) {
    result.status = "failed";
    result.error = e.message || String(e);
  }

  outputJSON(result);
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
