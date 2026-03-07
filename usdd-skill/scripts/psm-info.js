#!/usr/bin/env node

/**
 * psm-info.js — Read PSM state: fees, USDT reserves, and USDD total supply.
 *
 * No private key required.
 *
 * Usage:
 *   node psm-info.js
 */

const { CONTRACTS, getTronWebReadOnly, getNetwork, getContracts, resolveToken, fromSun, outputJSON, log } = require("./utils");

async function main() {
  const tronWeb = getTronWebReadOnly();
  const network = getNetwork();
  const contracts = getContracts();

  log(`Querying PSM state on ${network} ...`);

  const psmAddress = contracts.psm.address;
  const gemJoinAddress = contracts.psmGemJoin.address;

  // Query PSM fees (tin = buy fee, tout = sell fee)
  const psmContract = await tronWeb.contract(
    [CONTRACTS.abi.psm.tin, CONTRACTS.abi.psm.tout],
    psmAddress
  );

  const [tinRaw, toutRaw] = await Promise.all([
    psmContract.tin().call(),
    psmContract.tout().call(),
  ]);

  // tin/tout are WAD values (10^18 = 100%). 0 = zero fee.
  const tin = fromSun(BigInt(tinRaw), 18);
  const tout = fromSun(BigInt(toutRaw), 18);

  // Query USDT balance held by PSM GemJoin (available reserves)
  const usdt = resolveToken("USDT");
  const usdtContract = await tronWeb.contract(
    [CONTRACTS.abi.trc20.balanceOf],
    usdt.address
  );
  const usdtReserveRaw = await usdtContract.balanceOf(gemJoinAddress).call();
  const usdtReserve = fromSun(BigInt(usdtReserveRaw), usdt.decimals);

  // Query USDD total supply
  const usdd = resolveToken("USDD");
  const usddContract = await tronWeb.contract(
    [CONTRACTS.abi.trc20.totalSupply],
    usdd.address
  );
  const usddSupplyRaw = await usddContract.totalSupply().call();
  const usddTotalSupply = fromSun(BigInt(usddSupplyRaw), usdd.decimals);

  outputJSON({
    network,
    psm: {
      address: psmAddress,
      gem_join: gemJoinAddress,
    },
    fees: {
      tin,
      tout,
      tin_pct: (parseFloat(tin) * 100).toFixed(4) + "%",
      tout_pct: (parseFloat(tout) * 100).toFixed(4) + "%",
    },
    reserves: {
      usdt_available: usdtReserve,
    },
    usdd: {
      total_supply: usddTotalSupply,
    },
  });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
