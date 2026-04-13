#!/usr/bin/env node

/**
 * vault-info.js — Read vault (CDP) positions and protocol parameters.
 *
 * No private key required. Queries the Vat and DssCdpManager for vault data.
 *
 * Usage:
 *   node vault-info.js [--vault TRX-A] [--cdp <cdpId>]
 *
 * Modes:
 *   (no args)           Show global parameters for all vault types
 *   --vault TRX-A       Show parameters for a specific vault type
 *   --cdp 123           Show position for a specific CDP ID
 *
 * Examples:
 *   node vault-info.js
 *   node vault-info.js --vault TRX-A
 *   node vault-info.js --cdp 42
 */

const { CONTRACTS, getTronWebReadOnly, getNetwork, getContracts, getVaults, resolveVault, ilkToBytes32, fromSun, outputJSON, log } = require("./utils");

const RAY = BigInt(10) ** 27n;
const WAD = BigInt(10) ** 18n;

async function main() {
  const args = process.argv.slice(2);
  const tronWeb = getTronWebReadOnly();
  const network = getNetwork();
  const contracts = getContracts();

  // Parse flags
  let vaultFilter = null;
  let cdpId = null;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--vault" && i + 1 < args.length) vaultFilter = args[++i];
    if (args[i] === "--cdp" && i + 1 < args.length) cdpId = parseInt(args[++i], 10);
  }

  // If a specific CDP ID is provided, query its position
  if (cdpId !== null) {
    log(`Querying CDP #${cdpId} ...`);
    await queryCdp(tronWeb, contracts, cdpId);
    return;
  }

  // Otherwise, show vault type parameters
  const vaults = vaultFilter ? [resolveVault(vaultFilter)] : getVaults();
  log(`Querying vault parameters on ${network} ...`);

  const vatContract = await tronWeb.contract(
    [CONTRACTS.abi.vat.ilks],
    contracts.vat.address
  );

  const results = [];
  for (const vault of vaults) {
    try {
      const ilk = ilkToBytes32(vault.name);
      const ilkData = await vatContract.ilks(ilk).call();

      // ilkData: [Art, rate, spot, line, dust]
      const Art = BigInt(ilkData[0] || ilkData.Art || 0);
      const rate = BigInt(ilkData[1] || ilkData.rate || 0);
      const spot = BigInt(ilkData[2] || ilkData.spot || 0);
      const line = BigInt(ilkData[3] || ilkData.line || 0);
      const dust = BigInt(ilkData[4] || ilkData.dust || 0);

      // Total debt for this vault type = Art * rate / RAY (in WAD = 18 decimals)
      const totalDebt = rate > 0n ? (Art * rate) / RAY : 0n;

      results.push({
        name: vault.name,
        collateral: vault.collateral,
        gem_join: vault.gemJoin,
        stability_fee_pct: vault.stability_fee_pct,
        total_normalized_debt: fromSun(Art, 18),
        total_debt_usdd: fromSun(totalDebt, 18),
        rate: fromSun(rate, 27),
        spot: fromSun(spot, 27),
        debt_ceiling_usdd: fromSun(line / RAY, 18),
        dust_usdd: fromSun(dust / RAY, 18),
      });
    } catch (e) {
      results.push({
        name: vault.name,
        error: e.message,
      });
    }
  }

  outputJSON({ network, vaults: results });
}

async function queryCdp(tronWeb, contracts, cdpId) {
  const cdpManagerContract = await tronWeb.contract(
    [CONTRACTS.abi.cdpManager.urns, CONTRACTS.abi.cdpManager.ilks, CONTRACTS.abi.cdpManager.owns],
    contracts.cdpManager.address
  );

  // Get CDP info from manager
  const [urn, ilkBytes, owner] = await Promise.all([
    cdpManagerContract.urns(cdpId).call(),
    cdpManagerContract.ilks(cdpId).call(),
    cdpManagerContract.owns(cdpId).call(),
  ]);

  const urnAddress = tronWeb.address.fromHex(urn);
  const ownerAddress = tronWeb.address.fromHex(owner);

  // Decode ilk name from bytes32
  const ilkHex = typeof ilkBytes === "string" ? ilkBytes : ilkBytes.toString(16);
  const ilkClean = ilkHex.replace(/^0x/, "").replace(/0+$/, "");
  const ilkName = Buffer.from(ilkClean, "hex").toString("utf-8");

  // Query Vat for urn position
  const vatContract = await tronWeb.contract(
    [CONTRACTS.abi.vat.urns, CONTRACTS.abi.vat.ilks],
    contracts.vat.address
  );

  const [urnData, ilkData] = await Promise.all([
    vatContract.urns(ilkBytes, urn).call(),
    vatContract.ilks(ilkBytes).call(),
  ]);

  const ink = BigInt(urnData[0] || urnData.ink || 0); // collateral (WAD)
  const art = BigInt(urnData[1] || urnData.art || 0); // normalized debt (WAD)
  const rate = BigInt(ilkData[1] || ilkData.rate || 0);
  const spot = BigInt(ilkData[2] || ilkData.spot || 0);

  // Actual debt = art * rate / RAY
  const actualDebt = rate > 0n ? (art * rate) / RAY : 0n;

  // Max borrowable = ink * spot (in RAD = 10^45)
  // Collat ratio = (ink * spot) / (art * rate) if art > 0
  let collatRatio = "N/A";
  if (art > 0n && rate > 0n) {
    const collatValue = ink * spot; // RAD
    const debtValue = art * rate;   // RAD
    const ratioBps = (collatValue * 10000n) / debtValue;
    collatRatio = (Number(ratioBps) / 100).toFixed(2) + "%";
  }

  outputJSON({
    cdp_id: cdpId,
    owner: ownerAddress,
    urn: urnAddress,
    ilk: ilkName,
    collateral_locked: fromSun(ink, 18),
    normalized_debt: fromSun(art, 18),
    actual_debt_usdd: fromSun(actualDebt, 18),
    rate: fromSun(rate, 27),
    collateralization_ratio: collatRatio,
  });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
