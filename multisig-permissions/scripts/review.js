#!/usr/bin/env node

/**
 * review.js — Human-facing CLI for reviewing and co-signing agent proposals.
 *
 * Usage:
 *   node review.js                                     # List all pending proposals
 *   node review.js <proposal-id>                       # Inspect a proposal (read-only)
 *   node review.js <proposal-id> --sign                # Inspect + co-sign
 *   node review.js <proposal-id> --sign --execute      # Inspect + co-sign + broadcast
 *
 * Examples:
 *   node review.js
 *   node review.js prop_1710345600_b7e4
 *   node review.js prop_1710345600_b7e4 --sign
 *   node review.js prop_1710345600_b7e4 --sign --execute
 */

const { TronWeb } = require("tronweb");
const {
  loadProposal, saveProposal, archiveProposal,
  listProposals, getNetwork, outputJSON, log,
} = require("./utils");

function formatTimeRemaining(ms) {
  if (ms <= 0) return "EXPIRED";
  const hours = Math.floor(ms / (1000 * 60 * 60));
  const minutes = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));
  if (hours > 24) return `${Math.floor(hours / 24)}d ${hours % 24}h`;
  return `${hours}h ${minutes}m`;
}

function printProposalDetails(p) {
  const now = new Date();
  const expiresAt = new Date(p.expiresAt);
  const isExpired = expiresAt < now;
  const collectedWeight = p.signers.reduce((s, k) => s + k.weight, 0);
  const thresholdMet = collectedWeight >= p.threshold;

  log("");
  log("=== PROPOSAL DETAILS ===");
  log("");
  log(`  ID:          ${p.proposalId}`);
  log(`  Description: ${p.description}`);
  if (p.memo) log(`  Memo:        ${p.memo}`);
  log(`  Permission:  ${p.permission} (id=${p.permissionId})`);
  log(`  Created:     ${p.createdAt}`);
  log(`  Expires:     ${p.expiresAt} (${formatTimeRemaining(expiresAt - now)})`);
  log("");
  log("--- Signatures ---");
  log(`  Threshold:   ${p.threshold} (weight required)`);
  log(`  Collected:   ${collectedWeight}/${p.threshold} weight from ${p.signaturesCollected} signer(s)`);
  log(`  Status:      ${isExpired ? "EXPIRED" : thresholdMet ? "READY TO EXECUTE" : "AWAITING SIGNATURES"}`);
  log("");
  log("  Signers so far:");
  for (const s of p.signers) {
    log(`    - ${s.address} (weight ${s.weight})`);
  }
  log("");
  log("  All authorized keys:");
  for (const k of p.allKeys) {
    const signed = p.signers.some(s => s.address === k.address);
    log(`    - ${k.address} (weight ${k.weight}) ${signed ? "[SIGNED]" : "[pending]"}`);
  }
  log("");

  return { isExpired, thresholdMet, collectedWeight };
}

async function listMode() {
  const proposals = listProposals();

  if (proposals.length === 0) {
    log("No pending proposals.");
    log("The agent can create one with: node propose.js transfer <to> <amount>");
    outputJSON({ pending: [], total: 0 });
    return;
  }

  const now = new Date();
  const items = proposals.map(p => {
    const collectedWeight = p.signers.reduce((s, k) => s + k.weight, 0);
    const expiresAt = new Date(p.expiresAt);
    const isExpired = expiresAt < now;
    const thresholdMet = collectedWeight >= p.threshold;

    return {
      proposalId: p.proposalId,
      description: p.description,
      memo: p.memo || "",
      signatures: `${p.signaturesCollected}/${p.threshold}`,
      collected_weight: collectedWeight,
      required_weight: p.threshold,
      time_remaining: formatTimeRemaining(expiresAt - now),
      status: isExpired ? "expired" : thresholdMet ? "ready" : "awaiting",
      next_step: isExpired
        ? "Expired — create a new proposal"
        : thresholdMet
          ? `Execute: node review.js ${p.proposalId} --sign --execute`
          : `Review:  node review.js ${p.proposalId} --sign`,
    };
  });

  log(`Found ${items.length} pending proposal(s):\n`);
  for (const item of items) {
    log(`  [${item.status.toUpperCase()}] ${item.proposalId}`);
    log(`    ${item.description}`);
    log(`    Signatures: ${item.signatures} | Time left: ${item.time_remaining}`);
    log(`    -> ${item.next_step}`);
    log("");
  }

  outputJSON({ pending: items, total: items.length });
}

async function reviewMode(proposalRef, doSign, doExecute) {
  const proposal = loadProposal(proposalRef);

  // Always show details first
  let { isExpired, thresholdMet, collectedWeight } = printProposalDetails(proposal);

  if (isExpired) {
    outputJSON({ error: "Proposal has expired. Create a new one.", proposalId: proposal.proposalId });
    process.exit(1);
  }

  if (!doSign) {
    // Read-only mode — no private key required
    const result = {
      proposalId: proposal.proposalId,
      description: proposal.description,
      threshold_met: thresholdMet,
    };

    if (thresholdMet) {
      result.next_step = `Ready to execute: node review.js ${proposal.proposalId} --sign --execute`;
    } else {
      result.next_step = `To co-sign: node review.js ${proposal.proposalId} --sign`;
    }

    outputJSON(result);
    return;
  }

  // --- Sign mode (requires TRON_HUMAN_PRIVATE_KEY or TRON_PRIVATE_KEY) ---

  const humanKey = process.env.TRON_HUMAN_PRIVATE_KEY;
  if (!humanKey) {
    outputJSON({ error: "TRON_HUMAN_PRIVATE_KEY is required to sign. This must be the human co-signer's key, not the agent's TRON_PRIVATE_KEY." });
    process.exit(1);
  }
  const network = getNetwork();
  const mainnetHost = process.env.TRONGRID_API_KEY ? "https://api.trongrid.io" : "https://hptg.bankofai.io";
  const hosts = { mainnet: mainnetHost, nile: "https://nile.trongrid.io", shasta: "https://api.shasta.trongrid.io" };
  const opts = { fullHost: hosts[network], privateKey: humanKey };
  if (process.env.TRONGRID_API_KEY) opts.headers = { "TRON-PRO-API-KEY": process.env.TRONGRID_API_KEY };
  const tronWeb = new TronWeb(opts);
  const walletAddress = tronWeb.defaultAddress.base58;

  const isAuthorized = proposal.allKeys.some(k => k.address === walletAddress);
  if (!isAuthorized) {
    outputJSON({
      error: `Your address ${walletAddress} is not an authorized signer`,
      authorized_keys: proposal.allKeys.map(k => k.address),
    });
    process.exit(1);
  }

  const alreadySigned = proposal.signers.some(s => s.address === walletAddress);
  if (alreadySigned) {
    log(`You (${walletAddress}) have already signed this proposal.`);
  } else {
    log(`Signing proposal with ${walletAddress} ...`);
    const signed = await tronWeb.trx.multiSign(proposal.transaction, humanKey, proposal.permissionId);

    const signerWeight = proposal.allKeys.find(k => k.address === walletAddress)?.weight || 1;
    proposal.transaction = signed;
    proposal.signaturesCollected += 1;
    proposal.signers.push({ address: walletAddress, weight: signerWeight });
    saveProposal(proposal);

    collectedWeight = proposal.signers.reduce((s, k) => s + k.weight, 0);
    thresholdMet = collectedWeight >= proposal.threshold;

    log(`Signature added (weight ${signerWeight}). Total weight: ${collectedWeight}/${proposal.threshold}`);
    log("");
  }

  // --- Execute mode ---

  if (doExecute) {
    if (!thresholdMet) {
      outputJSON({
        error: `Cannot execute — threshold not met. Have weight ${collectedWeight}, need ${proposal.threshold}`,
        proposalId: proposal.proposalId,
        remaining_weight: proposal.threshold - collectedWeight,
      });
      process.exit(1);
    }

    log("Broadcasting transaction ...");
    try {
      const broadcast = await tronWeb.trx.sendRawTransaction(proposal.transaction);
      if (broadcast.result) {
        const archivedTo = archiveProposal(proposal.proposalId);
        log(`Transaction submitted: ${broadcast.txid}`);
        log(`Proposal archived to ${archivedTo}`);

        outputJSON({
          proposalId: proposal.proposalId,
          action: "signed_and_executed",
          signer: walletAddress,
          signatures: proposal.signaturesCollected,
          threshold: proposal.threshold,
          status: "submitted",
          tx_id: broadcast.txid,
          archived_to: archivedTo,
        });
      } else {
        outputJSON({
          proposalId: proposal.proposalId,
          status: "broadcast_failed",
          error: broadcast.message || broadcast.code || "Unknown error",
        });
        process.exit(1);
      }
    } catch (e) {
      outputJSON({ proposalId: proposal.proposalId, status: "failed", error: e.message || String(e) });
      process.exit(1);
    }
    return;
  }

  // Signed but not executing
  const result = {
    proposalId: proposal.proposalId,
    action: "signed",
    signer: walletAddress,
    signatures: {
      collected: proposal.signaturesCollected,
      collected_weight: collectedWeight,
      required_weight: proposal.threshold,
      threshold_met: thresholdMet,
    },
  };

  if (thresholdMet) {
    result.next_step = `Ready! Execute: node review.js ${proposal.proposalId} --sign --execute`;
  } else {
    result.next_step = `Need ${proposal.threshold - collectedWeight} more weight from other signers.`;
  }

  outputJSON(result);
}

async function main() {
  const args = process.argv.slice(2);

  // No args → list mode
  if (args.length === 0) {
    await listMode();
    return;
  }

  // Parse flags
  const doSign = args.includes("--sign");
  const doExecute = args.includes("--execute");
  const proposalRef = args.find(a => !a.startsWith("--"));

  if (!proposalRef) {
    await listMode();
    return;
  }

  if (doExecute && !doSign) {
    log("Warning: --execute requires --sign. Adding --sign automatically.");
  }

  await reviewMode(proposalRef, doSign || doExecute, doExecute);
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
