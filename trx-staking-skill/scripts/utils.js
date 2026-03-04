/**
 * Shared utilities for TRX Staking skill scripts.
 */

const { TronWeb } = require("tronweb");
const path = require("path");
const fs = require("fs");

const CONFIG = JSON.parse(
  fs.readFileSync(path.join(__dirname, "..", "resources", "staking_config.json"), "utf-8")
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

function fromSun(raw) {
  const str = String(raw).padStart(TRX_DECIMALS + 1, "0");
  const whole = str.slice(0, str.length - TRX_DECIMALS) || "0";
  const frac = str.slice(str.length - TRX_DECIMALS).replace(/0+$/, "");
  return frac ? `${whole}.${frac}` : whole;
}

function outputJSON(data) { process.stdout.write(JSON.stringify(data, null, 2) + "\n"); }
function log(msg) { process.stderr.write(msg + "\n"); }

module.exports = { CONFIG, TRX_DECIMALS, getTronWeb, fromSun, outputJSON, log };
