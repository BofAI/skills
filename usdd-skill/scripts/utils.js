/**
 * Shared utilities for USDD / JUST Protocol skill scripts.
 */

const { TronWeb } = require("tronweb");
const path = require("path");
const fs = require("fs");

const CONTRACTS = JSON.parse(
  fs.readFileSync(path.join(__dirname, "..", "resources", "usdd_contracts.json"), "utf-8")
);

function getNetwork() {
  return (process.env.TRON_NETWORK || "mainnet").toLowerCase();
}

function getTronWeb() {
  const network = getNetwork();
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
  const network = getNetwork();
  const hosts = { mainnet: "https://api.trongrid.io", nile: "https://nile.trongrid.io", shasta: "https://api.shasta.trongrid.io" };
  const fullHost = hosts[network];
  if (!fullHost) throw new Error(`Unknown network "${network}".`);
  const opts = { fullHost };
  if (process.env.TRONGRID_API_KEY) opts.headers = { "TRON-PRO-API-KEY": process.env.TRONGRID_API_KEY };
  const tw = new TronWeb(opts);
  // Set a zero-value default address so read-only contract calls have an owner_address
  tw.defaultAddress = {
    hex: "410000000000000000000000000000000000000000",
    base58: "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",
  };
  return tw;
}

/**
 * Resolve a token by symbol or address from CONTRACTS.tokens.
 * @param {string} symbolOrAddress - Token symbol (e.g. "USDD") or TRON address.
 * @returns {{ address: string|null, symbol: string, decimals: number, is_native?: boolean }}
 */
function resolveToken(symbolOrAddress) {
  const network = getNetwork();
  const tokens = CONTRACTS.tokens[network];
  if (!tokens) throw new Error(`No tokens configured for network "${network}".`);

  const bySymbol = Object.values(tokens).find(
    (t) => t.symbol.toLowerCase() === symbolOrAddress.toLowerCase()
  );
  if (bySymbol) return bySymbol;

  const byAddress = Object.values(tokens).find(
    (t) => t.address === symbolOrAddress
  );
  if (byAddress) return byAddress;

  throw new Error(
    `Unknown token "${symbolOrAddress}". Available: ${Object.values(tokens).map((t) => t.symbol).join(", ")}`
  );
}

/**
 * Resolve a vault by name from CONTRACTS.vaults.
 * @param {string} vaultName - Vault name (e.g. "TRX-A").
 * @returns {{ name: string, gemJoin: string, collateral: string, collateral_decimals: number, stability_fee_pct: number, is_native: boolean }}
 */
function resolveVault(vaultName) {
  const network = getNetwork();
  const vaults = CONTRACTS.vaults[network];
  if (!vaults) throw new Error(`No vaults configured for network "${network}".`);
  const match = vaults.find((v) => v.name.toLowerCase() === vaultName.toLowerCase());
  if (!match) throw new Error(`Unknown vault "${vaultName}". Available: ${vaults.map((v) => v.name).join(", ")}`);
  return match;
}

/**
 * Get all vault configs for the current network.
 */
function getVaults() {
  const network = getNetwork();
  return CONTRACTS.vaults[network] || [];
}

/**
 * Get contract addresses for the current network.
 */
function getContracts() {
  const network = getNetwork();
  const contracts = CONTRACTS.contracts[network];
  if (!contracts) throw new Error(`No contracts configured for network "${network}".`);
  return contracts;
}

/**
 * Encode a vault name (e.g. "TRX-A") as a bytes32 hex string.
 */
function ilkToBytes32(ilkName) {
  const hex = Buffer.from(ilkName, "utf-8").toString("hex");
  return "0x" + hex.padEnd(64, "0");
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

module.exports = {
  CONTRACTS,
  getTronWeb,
  getTronWebReadOnly,
  getNetwork,
  resolveToken,
  resolveVault,
  getVaults,
  getContracts,
  ilkToBytes32,
  toSun,
  fromSun,
  outputJSON,
  log,
};
