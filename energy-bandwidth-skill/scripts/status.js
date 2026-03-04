#!/usr/bin/env node

/**
 * status.js — Check current energy, bandwidth, and frozen TRX balances.
 *
 * Usage:
 *   node status.js [walletAddress]
 */

const { getTronWeb, fromSun, outputJSON, log } = require("./utils");

async function main() {
  const tronWeb = getTronWeb();
  const address = process.argv[2] || tronWeb.defaultAddress.base58;
  log(`Checking resources for ${address} ...`);

  const [resources, account, trxBalance] = await Promise.all([
    tronWeb.trx.getAccountResources(address),
    tronWeb.trx.getAccount(address),
    tronWeb.trx.getBalance(address),
  ]);

  const energyLimit = resources.EnergyLimit || 0;
  const energyUsed = resources.EnergyUsed || 0;
  const bwLimit = (resources.freeNetLimit || 0) + (resources.NetLimit || 0);
  const bwUsed = (resources.freeNetUsed || 0) + (resources.NetUsed || 0);

  const frozenV2 = account.frozenV2 || [];
  const frozenEnergy = frozenV2.find((f) => f.type === "ENERGY") || {};
  const frozenBandwidth = frozenV2.find((f) => !f.type || f.type === "BANDWIDTH") || {};

  const unfrozenV2 = account.unfrozenV2 || [];

  outputJSON({
    wallet: address,
    trx_balance: fromSun(trxBalance),
    energy: {
      available: energyLimit - energyUsed,
      limit: energyLimit,
      used: energyUsed,
      frozen_trx: fromSun(frozenEnergy.amount || 0),
    },
    bandwidth: {
      available: bwLimit - bwUsed,
      limit: bwLimit,
      used: bwUsed,
      free_limit: resources.freeNetLimit || 0,
      frozen_trx: fromSun(frozenBandwidth.amount || 0),
    },
    pending_unstakes: unfrozenV2.map((u) => ({
      amount_trx: fromSun(u.unfreeze_amount || 0),
      expire_time: u.unfreeze_expire_time ? new Date(u.unfreeze_expire_time).toISOString() : null,
      type: u.type || "BANDWIDTH",
    })),
  });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
