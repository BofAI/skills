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

function getMarkets() {
  const network = (process.env.TRON_NETWORK || "mainnet").toLowerCase();
  return CONTRACTS.markets[network] || [];
}

function getComptroller() {
  const network = (process.env.TRON_NETWORK || "mainnet").toLowerCase();
  return CONTRACTS.comptroller[network];
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

module.exports = { CONTRACTS, getTronWeb, getMarkets, getComptroller, resolveMarket, toSun, fromSun, outputJSON, log };
