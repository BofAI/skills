#!/usr/bin/env node

/**
 * position.js — Check supplied and borrowed amounts across JustLend markets.
 *
 * Usage:
 *   node position.js [walletAddress]
 */

const { CONTRACTS, HEALTH_FACTOR, getTronWeb, getTronWebReadOnly, getMarkets, getComptroller, fromSun, outputJSON, log, getHealthFactor } = require("./utils");

async function main() {
  const addressArg = process.argv[2];
  const tronWeb = addressArg ? getTronWebReadOnly() : getTronWeb();
  const address = addressArg || tronWeb.defaultAddress.base58;
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

  // Compute health factor
  let healthFactor = null;
  try {
    healthFactor = await getHealthFactor(tronWeb, address);
    if (healthFactor.health_factor !== null && healthFactor.health_factor !== Infinity) {
      log(`Health factor: ${healthFactor.health_factor}`);
      if (healthFactor.health_factor < HEALTH_FACTOR.min_threshold) {
        log(`CRITICAL: Health factor ${healthFactor.health_factor} is below minimum threshold ${HEALTH_FACTOR.min_threshold}. Liquidation risk is imminent!`);
      } else if (healthFactor.health_factor < HEALTH_FACTOR.warn_threshold) {
        log(`WARNING: Health factor ${healthFactor.health_factor} is below recommended safe level ${HEALTH_FACTOR.warn_threshold}.`);
      }
    }
  } catch (e) {
    healthFactor = { error: e.message };
  }

  outputJSON({ wallet: address, liquidity, health_factor: healthFactor, positions });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
