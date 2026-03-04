#!/usr/bin/env node

/**
 * position.js — Check supplied and borrowed amounts across JustLend markets.
 *
 * Usage:
 *   node position.js [walletAddress]
 */

const { CONTRACTS, getTronWeb, getMarkets, getComptroller, fromSun, outputJSON, log } = require("./utils");

async function main() {
  const tronWeb = getTronWeb();
  const address = process.argv[2] || tronWeb.defaultAddress.base58;
  const markets = getMarkets();
  const comptrollerAddr = getComptroller();

  log(`Checking JustLend positions for ${address} ...`);

  // Account liquidity from comptroller
  let liquidity = null;
  try {
    const comptroller = await tronWeb.contract(
      [CONTRACTS.abi.comptroller.getAccountLiquidity],
      comptrollerAddr
    );
    const liq = await comptroller.getAccountLiquidity(address).call();
    liquidity = {
      error_code: Number(liq[0]),
      excess_liquidity_usd: fromSun(liq[1], 18),
      shortfall_usd: fromSun(liq[2], 18),
    };
  } catch (e) {
    liquidity = { error: e.message };
  }

  const positions = [];
  for (const market of markets) {
    try {
      // Use view functions (exchangeRateStored, borrowBalanceStored) instead of
      // non-view variants (exchangeRateCurrent, borrowBalanceCurrent) because
      // TronWeb's .call() on non-view functions returns 0 instead of the actual value.
      const jContract = await tronWeb.contract(
        [
          CONTRACTS.abi.jToken.balanceOf,
          CONTRACTS.abi.jToken.exchangeRateStored,
          CONTRACTS.abi.jToken.borrowBalanceStored,
        ],
        market.jToken
      );

      const [jBalance, exchangeRate, borrowed] = await Promise.all([
        jContract.balanceOf(address).call(),
        jContract.exchangeRateStored().call(),
        jContract.borrowBalanceStored(address).call(),
      ]);

      if (Number(jBalance) === 0 && Number(borrowed) === 0) continue;

      // supplied = jBalance * exchangeRate / 1e18
      // exchangeRate is scaled to 18 + underlyingDecimals - jTokenDecimals
      const suppliedRaw = (BigInt(jBalance) * BigInt(exchangeRate)) / BigInt(10 ** 18);

      positions.push({
        symbol: market.symbol,
        jToken: market.jToken,
        jToken_balance: fromSun(jBalance, market.jDecimals),
        supplied: fromSun(suppliedRaw, market.decimals),
        borrowed: fromSun(borrowed, market.decimals),
      });
    } catch (e) {
      // Skip markets with errors
    }
  }

  outputJSON({ wallet: address, liquidity, positions });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
