/**
 * Shared utilities for TRC20 Toolkit skill scripts.
 */

const { TronWeb } = require("tronweb");
const path = require("path");
const fs = require("fs");

const TOKENS = JSON.parse(
  fs.readFileSync(
    path.join(__dirname, "..", "resources", "well_known_tokens.json"),
    "utf-8"
  )
);

const TRC20_ABI = [
  { type: "function", name: "name", inputs: [], outputs: [{ type: "string" }], stateMutability: "view" },
  { type: "function", name: "symbol", inputs: [], outputs: [{ type: "string" }], stateMutability: "view" },
  { type: "function", name: "decimals", inputs: [], outputs: [{ type: "uint8" }], stateMutability: "view" },
  { type: "function", name: "totalSupply", inputs: [], outputs: [{ type: "uint256" }], stateMutability: "view" },
  { type: "function", name: "balanceOf", inputs: [{ name: "account", type: "address" }], outputs: [{ type: "uint256" }], stateMutability: "view" },
  { type: "function", name: "transfer", inputs: [{ name: "to", type: "address" }, { name: "amount", type: "uint256" }], outputs: [{ type: "bool" }], stateMutability: "nonpayable" },
  { type: "function", name: "approve", inputs: [{ name: "spender", type: "address" }, { name: "amount", type: "uint256" }], outputs: [{ type: "bool" }], stateMutability: "nonpayable" },
  { type: "function", name: "allowance", inputs: [{ name: "owner", type: "address" }, { name: "spender", type: "address" }], outputs: [{ type: "uint256" }], stateMutability: "view" },
];

const MAX_UINT256 =
  "115792089237316195423570985008687907853269984665640564039457584007913129639935";

function getTronWeb() {
  const network = (process.env.TRON_NETWORK || "mainnet").toLowerCase();
  const hosts = { mainnet: "https://api.trongrid.io", nile: "https://nile.trongrid.io", shasta: "https://api.shasta.trongrid.io" };
  const fullHost = hosts[network];
  if (!fullHost) throw new Error(`Unknown network "${network}". Supported: ${Object.keys(hosts).join(", ")}`);
  const privateKey = process.env.TRON_PRIVATE_KEY;
  if (!privateKey) throw new Error("TRON_PRIVATE_KEY environment variable is required");
  const opts = { fullHost, privateKey };
  if (process.env.TRONGRID_API_KEY) opts.headers = { "TRON-PRO-API-KEY": process.env.TRONGRID_API_KEY };
  return new TronWeb(opts);
}

function resolveToken(symbolOrAddress) {
  if (symbolOrAddress.startsWith("T") && symbolOrAddress.length >= 34) return symbolOrAddress;
  const network = (process.env.TRON_NETWORK || "mainnet").toLowerCase();
  const net = TOKENS[network];
  if (!net) return symbolOrAddress;
  const match = net.find((t) => t.symbol.toLowerCase() === symbolOrAddress.toLowerCase());
  if (match) return match.address;
  throw new Error(`Unknown token symbol "${symbolOrAddress}". Use a contract address or one of: ${net.map((t) => t.symbol).join(", ")}`);
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

module.exports = { TOKENS, TRC20_ABI, MAX_UINT256, getTronWeb, resolveToken, toSun, fromSun, outputJSON, log };
