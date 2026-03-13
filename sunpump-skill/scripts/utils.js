/**
 * Shared utilities for SunPump skill scripts.
 */

const { TronWeb } = require("tronweb");
const path = require("path");
const fs = require("fs");

const CONTRACTS = JSON.parse(
  fs.readFileSync(
    path.join(__dirname, "..", "resources", "sunpump_contracts.json"),
    "utf-8"
  )
);

const TRX_DECIMALS = 6;
const TOKEN_DECIMALS = 18;
const MAX_UINT256 =
  "115792089237316195423570985008687907853269984665640564039457584007913129639935";

/**
 * Build a TronWeb instance from environment variables.
 */
function getTronWeb() {
  const network = (process.env.TRON_NETWORK || "mainnet").toLowerCase();
  const net = CONTRACTS.networks[network];
  if (!net) {
    throw new Error(
      `Unknown network "${network}". Supported: ${Object.keys(CONTRACTS.networks).join(", ")}`
    );
  }

  const fullHost = net.trongrid_api;
  const privateKey = process.env.TRON_PRIVATE_KEY;
  if (!privateKey) {
    throw new Error("TRON_PRIVATE_KEY environment variable is required");
  }

  const opts = { fullHost, privateKey };
  if (process.env.TRONGRID_API_KEY) {
    opts.headers = { "TRON-PRO-API-KEY": process.env.TRONGRID_API_KEY };
  }

  return new TronWeb(opts);
}

/**
 * Return the SunPump launcher address for the active network.
 */
function getLauncherAddress() {
  const network = (process.env.TRON_NETWORK || "mainnet").toLowerCase();
  return CONTRACTS.networks[network].sunpump_launcher.address;
}

/**
 * Convert a human-readable amount to on-chain integer (sun/wei).
 */
function toSun(amount, decimals = TRX_DECIMALS) {
  const parts = String(amount).split(".");
  const whole = parts[0] || "0";
  let frac = (parts[1] || "").slice(0, decimals).padEnd(decimals, "0");
  return BigInt(whole) * BigInt(10 ** decimals) + BigInt(frac);
}

/**
 * Convert an on-chain integer to human-readable string.
 */
function fromSun(raw, decimals = TRX_DECIMALS) {
  const str = String(raw).padStart(decimals + 1, "0");
  const whole = str.slice(0, str.length - decimals) || "0";
  const frac = str.slice(str.length - decimals).replace(/0+$/, "");
  return frac ? `${whole}.${frac}` : whole;
}

/**
 * Apply slippage to an amount. Returns the minimum acceptable amount.
 * @param {bigint|string} amount - The expected amount.
 * @param {number} slippagePercent - e.g. 5 for 5%.
 */
function applySlippage(amount, slippagePercent) {
  const raw = BigInt(amount);
  const factor = BigInt(Math.round((100 - slippagePercent) * 100));
  return (raw * factor) / 10000n;
}

/**
 * Output structured JSON to stdout (for agent consumption).
 */
function outputJSON(data) {
  process.stdout.write(JSON.stringify(data, null, 2) + "\n");
}

/**
 * Log human-readable messages to stderr (visible to user, not parsed by agent).
 */
function log(msg) {
  process.stderr.write(msg + "\n");
}

module.exports = {
  CONTRACTS,
  TRX_DECIMALS,
  TOKEN_DECIMALS,
  MAX_UINT256,
  getTronWeb,
  getLauncherAddress,
  toSun,
  fromSun,
  applySlippage,
  outputJSON,
  log,
};
