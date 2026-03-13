#!/usr/bin/env node

/**
 * estimate.js — Estimate energy cost for a smart contract call.
 *
 * Usage:
 *   node estimate.js <contractAddress> <functionSelector> [param1,param2,...] [callValue]
 *
 * Example:
 *   node estimate.js TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t "transfer(address,uint256)" "TRecipient,1000000"
 */

const { getTronWeb, outputJSON, log } = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error("Usage: node estimate.js <contract> <functionSelector> [params] [callValue]");
    process.exit(1);
  }

  const tronWeb = getTronWeb();
  const contractAddress = args[0];
  const functionSelector = args[1];
  const parameters = args[2] ? args[2].split(",").map((p) => p.trim()) : [];
  const callValue = args[3] ? Number(args[3]) : 0;
  const ownerAddress = tronWeb.defaultAddress.base58;

  log(`Estimating energy for ${functionSelector} on ${contractAddress} ...`);

  try {
    const tx = await tronWeb.transactionBuilder.triggerConstantContract(
      contractAddress,
      functionSelector,
      {},
      parameters.map((p, i) => ({ type: "auto", value: p })),
      ownerAddress
    );

    const energyUsed = tx.energy_used || tx.energy_penalty || 0;
    outputJSON({
      contract: contractAddress,
      function: functionSelector,
      estimated_energy: energyUsed,
      result: tx.constant_result ? tx.constant_result[0] : null,
    });
  } catch (e) {
    outputJSON({
      contract: contractAddress,
      function: functionSelector,
      error: e.message || String(e),
      note: "Estimation may fail for state-changing functions. Use triggerSmartContract for accurate estimates.",
    });
  }
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
