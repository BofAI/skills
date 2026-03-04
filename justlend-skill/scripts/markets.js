#!/usr/bin/env node

/**
 * markets.js — List available JustLend markets with APY rates.
 *
 * Usage:
 *   node markets.js
 */

const { CONTRACTS, getTronWeb, getMarkets, fromSun, outputJSON, log } = require("./utils");

const BLOCKS_PER_YEAR = 10_512_000;

async function main() {
  const tronWeb = getTronWeb();
  const markets = getMarkets();

  log("Fetching JustLend market rates ...");

  const results = [];
  for (const market of markets) {
    try {
      const jContract = await tronWeb.contract(
        [CONTRACTS.abi.jToken.supplyRatePerBlock, CONTRACTS.abi.jToken.borrowRatePerBlock],
        market.jToken
      );

      const [supplyRate, borrowRate] = await Promise.all([
        jContract.supplyRatePerBlock().call(),
        jContract.borrowRatePerBlock().call(),
      ]);

      const supplyAPY = ((1 + Number(supplyRate) / 1e18) ** BLOCKS_PER_YEAR - 1) * 100;
      const borrowAPY = ((1 + Number(borrowRate) / 1e18) ** BLOCKS_PER_YEAR - 1) * 100;

      results.push({
        symbol: market.symbol,
        jToken: market.jToken,
        supply_apy: supplyAPY.toFixed(2) + "%",
        borrow_apy: borrowAPY.toFixed(2) + "%",
        decimals: market.decimals,
      });
    } catch (e) {
      results.push({ symbol: market.symbol, error: e.message });
    }
  }

  outputJSON({ markets: results });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
