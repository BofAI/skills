/**
 * Shared utilities for JustLend skill scripts.
 */

const { TronWeb } = require("tronweb");
const path = require("path");
const fs = require("fs");

const CONTRACTS = JSON.parse(
  fs.readFileSync(path.join(__dirname, "..", "resources", "justlend_contracts.json"), "utf-8")
);

const TRX_DECIMALS = 6;
const HEALTH_FACTOR = CONTRACTS.health_factor;

function getTronWeb() {
  const network = (process.env.TRON_NETWORK || "mainnet").toLowerCase();
  const hosts = { mainnet: "https://api.trongrid.io", nile: "https://nile.trongrid.io", shasta: "https://api.shasta.trongrid.io" };
  const fullHost = hosts[network];
  if (!fullHost) throw new Error(`Unknown network "${network}".`);
  const privateKey = process.env.TRON_PRIVATE_KEY;
  if (!privateKey) throw new Error("TRON_PRIVATE_KEY environment variable is required");
  const opts = { fullHost, privateKey };
  if (process.env.TRONGRID_API_KEY) opts.headers = { "TRON-PRO-API-KEY": process.env.TRONGRID_API_KEY };
  return new TronWeb(opts);
}

function getTronWebReadOnly() {
  const network = (process.env.TRON_NETWORK || "mainnet").toLowerCase();
  const hosts = { mainnet: "https://api.trongrid.io", nile: "https://nile.trongrid.io", shasta: "https://api.shasta.trongrid.io" };
  const fullHost = hosts[network];
  if (!fullHost) throw new Error(`Unknown network "${network}".`);
  const opts = { fullHost };
  if (process.env.TRONGRID_API_KEY) opts.headers = { "TRON-PRO-API-KEY": process.env.TRONGRID_API_KEY };
  const tw = new TronWeb(opts);
  tw.defaultAddress = {
    hex: "410000000000000000000000000000000000000000",
    base58: "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",
  };
  return tw;
}

function getMarkets() {
  const network = (process.env.TRON_NETWORK || "mainnet").toLowerCase();
  return CONTRACTS.markets[network] || [];
}

function getComptroller() {
  const network = (process.env.TRON_NETWORK || "mainnet").toLowerCase();
  return CONTRACTS.comptroller[network];
}

function getPriceOracle() {
  const network = (process.env.TRON_NETWORK || "mainnet").toLowerCase();
  return CONTRACTS.price_oracle[network];
}

function resolveMarket(assetSymbol) {
  const markets = getMarkets();
  const match = markets.find((m) => m.symbol.toLowerCase() === assetSymbol.toLowerCase());
  if (!match) throw new Error(`Unknown asset "${assetSymbol}". Available: ${markets.map((m) => m.symbol).join(", ")}`);
  return match;
}

function toSun(amount, decimals) {
  const parts = String(amount).split(".");
  const whole = parts[0] || "0";
  const frac = (parts[1] || "").slice(0, decimals).padEnd(decimals, "0");
  return BigInt(whole) * BigInt(10 ** decimals) + BigInt(frac);
}

function fromSun(raw, decimals) {
  const str = String(raw).padStart(decimals + 1, "0");
  const whole = str.slice(0, str.length - decimals) || "0";
  const frac = str.slice(str.length - decimals).replace(/0+$/, "");
  return frac ? `${whole}.${frac}` : whole;
}

function outputJSON(data) { process.stdout.write(JSON.stringify(data, null, 2) + "\n"); }
function log(msg) { process.stderr.write(msg + "\n"); }

/**
 * Compute health factor from comptroller's getAccountLiquidity output.
 *
 * getAccountLiquidity returns (error, excessLiquidity, shortfall) in USD (18 decimals).
 * - If excessLiquidity > 0: account is solvent. We reconstruct HF from the liquidity values.
 * - If shortfall > 0: account is underwater (HF < 1).
 * - If both are 0 with no borrows: HF is Infinity (no risk).
 *
 * The comptroller defines: excessLiquidity = sumCollateral - sumBorrowPlusEffects
 * So: HF = sumCollateral / sumBorrows = (excessLiquidity + sumBorrows) / sumBorrows
 *
 * We also need sumBorrows to compute this. We get it by iterating positions.
 */
async function getHealthFactor(tronWeb, address) {
  const comptrollerAddr = getComptroller();
  const comptroller = await tronWeb.contract(
    [CONTRACTS.abi.comptroller.getAccountLiquidity],
    comptrollerAddr
  );
  const liq = await comptroller.getAccountLiquidity(address).call();
  const errCode = Number(liq[0]);
  const excessLiquidity = BigInt(liq[1]);
  const shortfall = BigInt(liq[2]);

  if (errCode !== 0) return { error: `Comptroller error code: ${errCode}`, health_factor: null };

  // Get total borrows in USD by summing across markets
  const markets = getMarkets();
  const oracleAddr = getPriceOracle();
  const oracle = await tronWeb.contract(
    [CONTRACTS.abi.priceOracle.getUnderlyingPrice],
    oracleAddr
  );

  let totalBorrowUSD = 0n;
  for (const market of markets) {
    try {
      const jContract = await tronWeb.contract(
        [CONTRACTS.abi.jToken.borrowBalanceStored],
        market.jToken
      );
      const borrowed = BigInt(await jContract.borrowBalanceStored(address).call());
      if (borrowed === 0n) continue;

      const price = BigInt(await oracle.getUnderlyingPrice(market.jToken).call());
      // price is scaled to 18 decimals in USD. borrowed is in underlying decimals.
      // borrowUSD = borrowed * price / 10^underlyingDecimals
      totalBorrowUSD += (borrowed * price) / BigInt(10 ** market.decimals);
    } catch (e) {
      // Skip markets with errors
    }
  }

  if (totalBorrowUSD === 0n) {
    return { health_factor: Infinity, excess_liquidity_usd: fromSun(excessLiquidity, 18), shortfall_usd: "0", total_borrow_usd: "0" };
  }

  // HF = (excessLiquidity + totalBorrowUSD) / totalBorrowUSD  (when no shortfall)
  // HF = (totalBorrowUSD - shortfall) / totalBorrowUSD         (when shortfall > 0)
  let hf;
  if (shortfall > 0n) {
    const collateralUSD = totalBorrowUSD - shortfall;
    hf = Number(collateralUSD * 10000n / totalBorrowUSD) / 10000;
  } else {
    const collateralUSD = excessLiquidity + totalBorrowUSD;
    hf = Number(collateralUSD * 10000n / totalBorrowUSD) / 10000;
  }

  return {
    health_factor: Math.round(hf * 100) / 100,
    excess_liquidity_usd: fromSun(excessLiquidity, 18),
    shortfall_usd: fromSun(shortfall, 18),
    total_borrow_usd: fromSun(totalBorrowUSD, 18),
  };
}

/**
 * Estimate health factor after a new borrow.
 * Uses current account liquidity and subtracts the new borrow's USD value.
 */
async function estimateHealthFactorAfterBorrow(tronWeb, address, borrowMarket, borrowAmountRaw) {
  const comptrollerAddr = getComptroller();
  const comptroller = await tronWeb.contract(
    [CONTRACTS.abi.comptroller.getAccountLiquidity],
    comptrollerAddr
  );
  const liq = await comptroller.getAccountLiquidity(address).call();
  const errCode = Number(liq[0]);
  const excessLiquidity = BigInt(liq[1]);
  const shortfall = BigInt(liq[2]);

  if (errCode !== 0) return { error: `Comptroller error code: ${errCode}`, estimated_health_factor: null };

  // Get oracle price for the borrow asset
  const oracleAddr = getPriceOracle();
  const oracle = await tronWeb.contract(
    [CONTRACTS.abi.priceOracle.getUnderlyingPrice],
    oracleAddr
  );
  const price = BigInt(await oracle.getUnderlyingPrice(borrowMarket.jToken).call());
  const newBorrowUSD = (BigInt(borrowAmountRaw) * price) / BigInt(10 ** borrowMarket.decimals);

  // Get current total borrows in USD
  const markets = getMarkets();
  let totalBorrowUSD = 0n;
  for (const market of markets) {
    try {
      const jContract = await tronWeb.contract(
        [CONTRACTS.abi.jToken.borrowBalanceStored],
        market.jToken
      );
      const borrowed = BigInt(await jContract.borrowBalanceStored(address).call());
      if (borrowed === 0n) continue;
      const mPrice = BigInt(await oracle.getUnderlyingPrice(market.jToken).call());
      totalBorrowUSD += (borrowed * mPrice) / BigInt(10 ** market.decimals);
    } catch (e) { /* skip */ }
  }

  const newTotalBorrowUSD = totalBorrowUSD + newBorrowUSD;
  if (newTotalBorrowUSD === 0n) {
    return { estimated_health_factor: Infinity, new_borrow_usd: fromSun(newBorrowUSD, 18) };
  }

  // Current collateral = excessLiquidity + totalBorrowUSD (or totalBorrowUSD - shortfall)
  let collateralUSD;
  if (shortfall > 0n) {
    collateralUSD = totalBorrowUSD - shortfall;
  } else {
    collateralUSD = excessLiquidity + totalBorrowUSD;
  }

  const hf = Number(collateralUSD * 10000n / newTotalBorrowUSD) / 10000;

  return {
    estimated_health_factor: Math.round(hf * 100) / 100,
    current_borrow_usd: fromSun(totalBorrowUSD, 18),
    new_borrow_usd: fromSun(newBorrowUSD, 18),
    total_borrow_usd_after: fromSun(newTotalBorrowUSD, 18),
    collateral_usd: fromSun(collateralUSD, 18),
  };
}

/**
 * Check health factor against configured thresholds.
 * Blocks execution if below min_threshold, warns if below warn_threshold.
 */
function checkHealthFactorThreshold(hf, context) {
  if (hf === Infinity) return; // no borrows, safe
  if (hf < HEALTH_FACTOR.min_threshold) {
    outputJSON({
      error: `Health factor safeguard: ${context} would result in a health factor of ${hf}, which is below the minimum threshold of ${HEALTH_FACTOR.min_threshold}. Reduce the borrow amount or supply more collateral.`,
      estimated_health_factor: hf,
      min_threshold: HEALTH_FACTOR.min_threshold,
    });
    process.exit(1);
  }
  if (hf < HEALTH_FACTOR.warn_threshold) {
    log(`WARNING: ${context} will result in a health factor of ${hf}, which is below the recommended safe level of ${HEALTH_FACTOR.warn_threshold}. Liquidation risk is elevated.`);
  }
}

module.exports = { CONTRACTS, HEALTH_FACTOR, getTronWeb, getTronWebReadOnly, getMarkets, getComptroller, getPriceOracle, resolveMarket, toSun, fromSun, outputJSON, log, getHealthFactor, estimateHealthFactorAfterBorrow, checkHealthFactorThreshold };
