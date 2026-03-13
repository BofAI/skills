#!/usr/bin/env node

/**
 * info.js — Get TRC20 token metadata.
 *
 * Usage:
 *   node info.js <tokenAddressOrSymbol>
 *
 * Environment:
 *   TRON_PRIVATE_KEY, TRON_NETWORK (mainnet|nile), TRONGRID_API_KEY (optional)
 */

const { TRC20_ABI, getTronWeb, resolveToken, fromSun, outputJSON, log } = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) { console.error("Usage: node info.js <tokenAddressOrSymbol>"); process.exit(1); }

  const tronWeb = getTronWeb();
  const tokenAddress = resolveToken(args[0]);
  log(`Fetching metadata for ${tokenAddress} ...`);

  const contract = await tronWeb.contract(TRC20_ABI, tokenAddress);
  const [name, symbol, decimals, totalSupply] = await Promise.all([
    contract.name().call(),
    contract.symbol().call(),
    contract.decimals().call(),
    contract.totalSupply().call(),
  ]);

  const dec = Number(decimals);
  outputJSON({
    address: tokenAddress,
    name: String(name),
    symbol: String(symbol),
    decimals: dec,
    total_supply: fromSun(totalSupply, dec),
    total_supply_raw: String(totalSupply),
  });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
