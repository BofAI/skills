#!/usr/bin/env node

/**
 * propose.js — Create a multi-sig transaction proposal.
 *
 * Builds a transaction, partially signs it with the caller's key,
 * and saves it to ~/.clawdbot/multisig/pending/ for co-signers.
 *
 * Usage:
 *   node propose.js transfer <to> <amount> [--permission owner|active] [--memo "..."]
 *   node propose.js trc20-transfer <token> <to> <amount> [--permission owner|active] [--memo "..."]
 *   node propose.js contract-call <contract> <function-sig> <args-json> [--permission owner|active] [--memo "..."]
 *
 * Examples:
 *   node propose.js transfer TRecipient... 10000 --memo "Monthly budget"
 *   node propose.js trc20-transfer TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t TRecipient... 500 --memo "USDT payment"
 *   node propose.js contract-call TContractAddr... "transfer(address,uint256)" '["TTo...", "1000000"]' --permission active
 */

const { TronWeb } = require("tronweb");
const {
  getTronWeb, toSun, fromSun, generateProposalId, saveProposal,
  outputJSON, log,
} = require("./utils");

function toBase58(addr) {
  try { return TronWeb.address.fromHex(addr); } catch { return addr; }
}

function parseArgs() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error("Usage: node propose.js <transfer|trc20-transfer|contract-call> <args> [--options]");
    process.exit(1);
  }

  const txType = args[0];
  const positional = [];
  const flags = { permission: "owner", memo: "" };

  for (let i = 1; i < args.length; i++) {
    if (args[i] === "--permission" && args[i + 1]) { flags.permission = args[++i]; continue; }
    if (args[i] === "--memo" && args[i + 1]) { flags.memo = args[++i]; continue; }
    if (args[i] === "--expiry" && args[i + 1]) { flags.expiryHours = Number(args[++i]); continue; }
    if (!args[i].startsWith("--")) positional.push(args[i]);
  }

  return { txType, positional, ...flags };
}

async function main() {
  const opts = parseArgs();
  const tronWeb = getTronWeb();
  const walletAddress = tronWeb.defaultAddress.base58;

  // Determine permission ID
  const permissionId = opts.permission === "active" ? 2 : 0;
  const permLabel = permissionId === 0 ? "owner" : "active";

  // Fetch account to know threshold
  const account = await tronWeb.trx.getAccount(walletAddress);
  if (!account || !account.address) {
    outputJSON({ error: `Account not found or not activated: ${walletAddress}` });
    process.exit(1);
  }

  let threshold;
  let permKeys;
  if (permissionId === 0) {
    const perm = account.owner_permission || { threshold: 1, keys: [{ address: walletAddress, weight: 1 }] };
    threshold = perm.threshold || 1;
    permKeys = perm.keys || [];
  } else {
    const actives = account.active_permission || [];
    const perm = actives.find(p => p.id === permissionId);
    if (!perm) { outputJSON({ error: `Active permission id=${permissionId} not found` }); process.exit(1); }
    threshold = perm.threshold || 1;
    permKeys = perm.keys || [];
  }

  log(`Building ${opts.txType} transaction (permission: ${permLabel}, threshold: ${threshold}) ...`);

  let tx;
  let description;

  switch (opts.txType) {
    case "transfer": {
      const to = opts.positional[0];
      const amountTrx = opts.positional[1];
      if (!to || !amountTrx) { outputJSON({ error: "Usage: node propose.js transfer <to> <amount>" }); process.exit(1); }
      const amountSun = Number(toSun(amountTrx));
      tx = await tronWeb.transactionBuilder.sendTrx(to, amountSun, walletAddress);
      description = `Transfer ${amountTrx} TRX to ${to}`;
      break;
    }

    case "trc20-transfer": {
      const tokenAddr = opts.positional[0];
      const to = opts.positional[1];
      const amount = opts.positional[2];
      if (!tokenAddr || !to || !amount) {
        outputJSON({ error: "Usage: node propose.js trc20-transfer <tokenAddress> <to> <amount>" });
        process.exit(1);
      }
      // Encode transfer(address,uint256) call
      const parameter = [
        { type: "address", value: to },
        { type: "uint256", value: amount },
      ];
      tx = await tronWeb.transactionBuilder.triggerSmartContract(
        tokenAddr, "transfer(address,uint256)", {},
        parameter, walletAddress
      );
      tx = tx.transaction;
      description = `TRC20 transfer ${amount} of ${tokenAddr} to ${to}`;
      break;
    }

    case "contract-call": {
      const contract = opts.positional[0];
      const functionSig = opts.positional[1];
      const argsJson = opts.positional[2] || "[]";
      if (!contract || !functionSig) {
        outputJSON({ error: "Usage: node propose.js contract-call <contract> <function-sig> [args-json]" });
        process.exit(1);
      }
      let callArgs;
      try { callArgs = JSON.parse(argsJson); } catch { callArgs = []; }

      // Parse function signature to extract parameter types
      const paramMatch = functionSig.match(/\(([^)]*)\)/);
      const paramTypes = paramMatch && paramMatch[1] ? paramMatch[1].split(",") : [];
      const parameter = paramTypes.map((type, i) => ({
        type: type.trim(),
        value: callArgs[i],
      }));

      tx = await tronWeb.transactionBuilder.triggerSmartContract(
        contract, functionSig, {},
        parameter, walletAddress
      );
      tx = tx.transaction;
      description = `Call ${functionSig} on ${contract}`;
      break;
    }

    default:
      outputJSON({ error: `Unknown tx type: "${opts.txType}". Use: transfer, trc20-transfer, contract-call` });
      process.exit(1);
  }

  // Extend transaction expiration for multi-sig (default ~10s is too short)
  const expiryMs = (opts.expiryHours || 24) * 60 * 60 * 1000;
  const expirySeconds = Math.floor(expiryMs / 1000);
  tx = await tronWeb.transactionBuilder.extendExpiration(tx, expirySeconds);

  // Sign with caller's key using multiSign (which handles Permission_id internally)
  log("Signing with caller key ...");
  const signed = await tronWeb.trx.multiSign(tx, undefined, permissionId);

  // Build proposal
  const proposalId = generateProposalId();
  const now = Date.now();

  const proposal = {
    proposalId,
    description,
    memo: opts.memo || "",
    permission: permLabel,
    permissionId,
    threshold,
    signaturesCollected: 1,
    createdAt: new Date(now).toISOString(),
    expiresAt: new Date(now + expiryMs).toISOString(),
    signers: [{ address: walletAddress, weight: permKeys.find(k => toBase58(k.address) === walletAddress)?.weight || 1 }],
    allKeys: permKeys.map(k => ({ address: toBase58(k.address), weight: k.weight || 1 })),
    transaction: signed,
  };

  const filePath = saveProposal(proposal);
  log(`Proposal saved to ${filePath}`);

  // Calculate collected weight
  const collectedWeight = proposal.signers.reduce((s, k) => s + k.weight, 0);

  outputJSON({
    proposalId,
    description,
    memo: opts.memo || "",
    permission: permLabel,
    threshold,
    signatures: {
      collected: 1,
      collected_weight: collectedWeight,
      required_weight: threshold,
      threshold_met: collectedWeight >= threshold,
    },
    expires: proposal.expiresAt,
    saved_to: filePath,
    next_step: collectedWeight >= threshold
      ? `Ready to execute: node execute.js ${proposalId}`
      : `Share proposal ID with co-signers: node approve.js ${proposalId}`,
  });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
