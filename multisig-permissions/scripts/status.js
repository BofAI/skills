#!/usr/bin/env node

/**
 * status.js — View current account permission configuration.
 *
 * Usage:
 *   node status.js [address]
 *
 * If no address is given, inspects the caller's wallet.
 *
 * Examples:
 *   node status.js
 *   node status.js TXk8rQSAvPvBBNtqSoY3UkFdpMTMbqRMKU
 */

const { TronWeb } = require("tronweb");
const {
  getTronWeb, getTronWebReadOnly, getAccountInfo, decodeOperations, getEnabledOperationBitCount, classifySecurity,
  formatPermConfig, outputJSON, log,
} = require("./utils");

function toBase58(addr) {
  try { return TronWeb.address.fromHex(addr); } catch { return addr; }
}

function formatKeys(keys) {
  return (keys || []).map(k => ({
    address: toBase58(k.address),
    weight: k.weight || 1,
  }));
}

async function main() {
  const targetAddress = process.argv[2];

  let tronWeb;
  let address;

  if (targetAddress) {
    tronWeb = getTronWebReadOnly();
    address = targetAddress;
  } else {
    tronWeb = getTronWeb();
    address = tronWeb.defaultAddress.base58;
  }

  log(`Checking permissions for ${address} ...`);

  const account = await getAccountInfo(tronWeb, address);
  if (!account || !account.address) {
    outputJSON({ error: `Account not found or not activated: ${address}` });
    process.exit(1);
  }

  // --- Owner permission ---
  const ownerPerm = account.owner_permission || {
    type: 0,
    permission_name: "owner",
    threshold: 1,
    keys: [{ address, weight: 1 }],
  };
  const ownerKeys = formatKeys(ownerPerm.keys);
  const ownerThreshold = ownerPerm.threshold || 1;

  // --- Active permissions ---
  const rawActive = account.active_permission || [];
  const activePerms = rawActive.map(p => {
    const keys = formatKeys(p.keys);
    const threshold = p.threshold || 1;
    const ops = decodeOperations(p.operations);
    const enabledBits = getEnabledOperationBitCount(p.operations);
    return {
      id: p.id,
      name: p.permission_name || `active:${p.id}`,
      threshold,
      keys,
      is_multisig: threshold > 1 || keys.length > 1,
      config: formatPermConfig(keys, threshold),
      operations: ops,
      operations_recognized: ops.length,
      operations_enabled_bits: enabledBits,
      operations_hex: p.operations || null,
    };
  });

  // --- Witness permission ---
  const witnessPerm = account.witness_permission || null;
  let witnessOut = null;
  if (witnessPerm) {
    const wKeys = formatKeys(witnessPerm.keys);
    witnessOut = {
      threshold: witnessPerm.threshold || 1,
      keys: wKeys,
      url: witnessPerm.url || null,
    };
  }

  // --- Security analysis ---
  const { level, notes } = classifySecurity(ownerPerm, rawActive);

  outputJSON({
    address,
    network: (process.env.TRON_NETWORK || "mainnet").toLowerCase(),
    owner: {
      threshold: ownerThreshold,
      keys: ownerKeys,
      is_multisig: ownerThreshold > 1 || ownerKeys.length > 1,
      config: formatPermConfig(ownerKeys, ownerThreshold),
    },
    active: activePerms,
    witness: witnessOut,
    security_level: level,
    analysis: notes,
  });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
