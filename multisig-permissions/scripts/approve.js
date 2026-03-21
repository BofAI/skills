#!/usr/bin/env node

/**
 * approve.js — Add a signature to a pending multi-sig proposal.
 *
 * Usage:
 *   node approve.js <proposal-id>
 *   node approve.js <path/to/proposal.json>
 *
 * Examples:
 *   node approve.js prop_1709312400_a3f2
 *   node approve.js ~/.clawdbot/multisig/pending/prop_1709312400_a3f2.json
 */

const {
  getTronWeb, loadProposal, saveProposal, outputJSON, log,
} = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error("Usage: node approve.js <proposal-id-or-file>");
    process.exit(1);
  }

  const tronWeb = getTronWeb();
  const walletAddress = tronWeb.defaultAddress.base58;
  const proposalRef = args[0];

  log(`Loading proposal "${proposalRef}" ...`);
  const proposal = loadProposal(proposalRef);

  // Display proposal details
  log("");
  log(`  Proposal:    ${proposal.proposalId}`);
  log(`  Description: ${proposal.description}`);
  if (proposal.memo) log(`  Memo:        ${proposal.memo}`);
  log(`  Permission:  ${proposal.permission} (id=${proposal.permissionId})`);
  log(`  Threshold:   ${proposal.threshold}`);
  log(`  Signatures:  ${proposal.signaturesCollected}/${proposal.threshold}`);
  log(`  Expires:     ${proposal.expiresAt}`);
  log("");

  // Check expiry
  if (new Date(proposal.expiresAt) < new Date()) {
    outputJSON({ error: "Proposal has expired", proposalId: proposal.proposalId, expiredAt: proposal.expiresAt });
    process.exit(1);
  }

  // Check caller is an authorized signer
  const isAuthorized = proposal.allKeys.some(k => k.address === walletAddress);
  if (!isAuthorized) {
    outputJSON({
      error: `Your address ${walletAddress} is not an authorized signer for this proposal`,
      authorized_keys: proposal.allKeys.map(k => k.address),
    });
    process.exit(1);
  }

  // Check if already signed
  const alreadySigned = proposal.signers.some(s => s.address === walletAddress);
  if (alreadySigned) {
    outputJSON({
      error: `You have already signed this proposal`,
      proposalId: proposal.proposalId,
      your_address: walletAddress,
    });
    process.exit(1);
  }

  // Add signature (TronWeb v6 uses multiSign instead of addSign)
  log(`Signing with ${walletAddress} ...`);
  const privateKey = process.env.TRON_PRIVATE_KEY;
  const signed = await tronWeb.trx.multiSign(proposal.transaction, privateKey, proposal.permissionId);

  // Update proposal
  const signerWeight = proposal.allKeys.find(k => k.address === walletAddress)?.weight || 1;
  proposal.transaction = signed;
  proposal.signaturesCollected += 1;
  proposal.signers.push({ address: walletAddress, weight: signerWeight });

  // Calculate total collected weight
  const collectedWeight = proposal.signers.reduce((s, k) => s + k.weight, 0);
  const thresholdMet = collectedWeight >= proposal.threshold;

  // Save updated proposal
  saveProposal(proposal);
  log("Proposal updated and saved.");

  outputJSON({
    proposalId: proposal.proposalId,
    description: proposal.description,
    approved: true,
    signer: walletAddress,
    signer_weight: signerWeight,
    signatures: {
      collected: proposal.signaturesCollected,
      collected_weight: collectedWeight,
      required_weight: proposal.threshold,
      threshold_met: thresholdMet,
    },
    ready_to_execute: thresholdMet,
    next_step: thresholdMet
      ? `Execute now: node execute.js ${proposal.proposalId}`
      : `Need more signatures (weight ${proposal.threshold - collectedWeight} remaining)`,
  });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
