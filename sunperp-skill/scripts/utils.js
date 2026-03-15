import crypto from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const CONFIG = JSON.parse(
  readFileSync(join(__dirname, "..", "resources", "sunperp_config.json"), "utf8")
);
const BASE_URL = CONFIG.api.base_url;
const SAFETY = CONFIG.safety;

// ---------------------------------------------------------------------------
// Environment helpers
// ---------------------------------------------------------------------------

export function getCredentials() {
  const accessKey = process.env.SUNPERP_ACCESS_KEY;
  const secretKey = process.env.SUNPERP_SECRET_KEY;
  if (!accessKey || !secretKey) {
    throw new Error(
      "Missing SUNPERP_ACCESS_KEY or SUNPERP_SECRET_KEY environment variables. " +
      `Create API keys at ${CONFIG.api.api_manage_url}`
    );
  }
  return { accessKey, secretKey };
}

// ---------------------------------------------------------------------------
// Timestamp
// ---------------------------------------------------------------------------

function utcTimestamp() {
  // Format: YYYY-MM-DDThh:mm:ss
  return new Date().toISOString().replace(/\.\d{3}Z$/, "");
}

// ---------------------------------------------------------------------------
// Signature (HmacSHA256)
// ---------------------------------------------------------------------------

function buildSignaturePayload(method, path, sortedParams) {
  const paramString = sortedParams
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&");
  return `${method}\napi.sunx.io\n${path}\n${paramString}`;
}

function sign(secretKey, payload) {
  return crypto
    .createHmac("sha256", secretKey)
    .update(payload, "utf8")
    .digest("base64");
}

function buildAuthParams(accessKey) {
  return {
    AccessKeyId: accessKey,
    SignatureMethod: "HmacSHA256",
    SignatureVersion: "2",
    Timestamp: utcTimestamp(),
  };
}

// ---------------------------------------------------------------------------
// Request helpers
// ---------------------------------------------------------------------------

export async function publicGet(path, params = {}) {
  const qs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== "")
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&");
  const url = `${BASE_URL}${path}${qs ? "?" + qs : ""}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function privateGet(path, params = {}) {
  const { accessKey, secretKey } = getCredentials();
  const authParams = buildAuthParams(accessKey);

  const allParams = { ...params, ...authParams };
  // Remove undefined/null
  for (const k of Object.keys(allParams)) {
    if (allParams[k] === undefined || allParams[k] === null || allParams[k] === "") {
      delete allParams[k];
    }
  }

  const sorted = Object.entries(allParams).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
  const payload = buildSignaturePayload("GET", path, sorted);
  const signature = sign(secretKey, payload);

  const qs = sorted
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&") + `&Signature=${encodeURIComponent(signature)}`;

  const url = `${BASE_URL}${path}?${qs}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function privatePost(path, params = {}, body = {}) {
  const { accessKey, secretKey } = getCredentials();
  const authParams = buildAuthParams(accessKey);

  // Query params for signature (auth params only for POST)
  const queryParams = { ...authParams };
  const sorted = Object.entries(queryParams).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
  const payload = buildSignaturePayload("POST", path, sorted);
  const signature = sign(secretKey, payload);

  const qs = sorted
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&") + `&Signature=${encodeURIComponent(signature)}`;

  const url = `${BASE_URL}${path}?${qs}`;

  // Clean body
  const cleanBody = {};
  for (const [k, v] of Object.entries(body)) {
    if (v !== undefined && v !== null && v !== "") {
      cleanBody[k] = v;
    }
  }

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cleanBody),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function walletPost(path, body = {}) {
  const { accessKey, secretKey } = getCredentials();
  const authParams = buildAuthParams(accessKey);

  // Wallet endpoints: signature path excludes /sapi/v1 prefix
  const signPath = path.replace(/^\/sapi\/v1/, "");

  const sorted = Object.entries(authParams).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
  const payload = buildSignaturePayload("POST", signPath, sorted);
  const signature = sign(secretKey, payload);

  const qs = sorted
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&") + `&Signature=${encodeURIComponent(signature)}`;

  const url = `${BASE_URL}${path}?${qs}`;

  const cleanBody = {};
  for (const [k, v] of Object.entries(body)) {
    if (v !== undefined && v !== null && v !== "") {
      cleanBody[k] = v;
    }
  }

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "CLOUD-EXCHANGE": CONFIG.api.wallet_header["CLOUD-EXCHANGE"],
    },
    body: JSON.stringify(cleanBody),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function walletGet(path, params = {}) {
  const { accessKey, secretKey } = getCredentials();
  const authParams = buildAuthParams(accessKey);

  const signPath = path.replace(/^\/sapi\/v1/, "");
  const allParams = { ...params, ...authParams };
  for (const k of Object.keys(allParams)) {
    if (allParams[k] === undefined || allParams[k] === null || allParams[k] === "") {
      delete allParams[k];
    }
  }

  const sorted = Object.entries(allParams).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
  const payload = buildSignaturePayload("GET", signPath, sorted);
  const signature = sign(secretKey, payload);

  const qs = sorted
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&") + `&Signature=${encodeURIComponent(signature)}`;

  const url = `${BASE_URL}${path}?${qs}`;
  const res = await fetch(url, {
    headers: {
      "CLOUD-EXCHANGE": CONFIG.api.wallet_header["CLOUD-EXCHANGE"],
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Output helpers
// ---------------------------------------------------------------------------

export function printJson(data) {
  console.log(JSON.stringify(data, null, 2));
}

export function exitWithError(msg) {
  console.error(`ERROR: ${msg}`);
  process.exit(1);
}

export function parseArgs(argv, required = [], optional = []) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const [key, ...rest] = argv[i].split("=");
    args[key] = rest.join("=") || "true";
  }
  for (const r of required) {
    if (!(r in args)) {
      exitWithError(
        `Missing required argument: ${r}\n` +
        `Usage: node <script> ${required.map((r) => `${r}=<value>`).join(" ")} ` +
        `${optional.map((o) => `[${o}=<value>]`).join(" ")}`
      );
    }
  }
  return args;
}

// ---------------------------------------------------------------------------
// Safety enforcement
// ---------------------------------------------------------------------------

/**
 * Validate leverage against the configured max_leverage cap.
 * Exits with an error if the requested leverage exceeds the limit.
 */
export function validateLeverage(leverRate) {
  const max = SAFETY.max_leverage;
  if (leverRate > max) {
    exitWithError(
      `Leverage ${leverRate}x exceeds the agent safety cap of ${max}x. ` +
      `Adjust max_leverage in sunperp_config.json to raise this limit.`
    );
  }
}

/**
 * Enforce mandatory stop-loss on position-opening orders.
 * If sl_trigger_price is already set, validates it's within max_percent of the reference price.
 * If omitted and required=true, auto-calculates one at default_percent from the reference price.
 *
 * @param {object} orderBody - the order body being built (mutated in place)
 * @param {number|null} referencePrice - the limit price or current market price
 */
export function enforceStopLoss(orderBody, referencePrice) {
  const sl = SAFETY.stop_loss;
  if (!sl.required) return;

  // Only enforce on position-opening orders (not reduce_only / close)
  if (orderBody.reduce_only === 1) return;

  const side = orderBody.side; // buy = long, sell = short
  const price = orderBody.sl_trigger_price;

  if (price != null) {
    // Validate the user-supplied stop-loss is within max_percent
    if (referencePrice) {
      const distance = Math.abs(price - referencePrice) / referencePrice * 100;
      if (distance > sl.max_percent) {
        exitWithError(
          `Stop-loss distance of ${distance.toFixed(1)}% exceeds the maximum allowed ${sl.max_percent}%. ` +
          `Set a tighter sl_trigger_price.`
        );
      }
    }
    return;
  }

  // Auto-calculate stop-loss if omitted
  if (!referencePrice) {
    // For market orders without a reference price, we can't auto-calculate.
    // The agent MUST provide sl_trigger_price for market orders.
    exitWithError(
      "Stop-loss is required for all position-opening orders. " +
      "For market orders, provide sl_trigger_price explicitly (e.g., sl_trigger_price=90000)."
    );
    return;
  }

  const pct = sl.default_percent / 100;
  if (side === "buy") {
    // Long: stop-loss below entry
    orderBody.sl_trigger_price = Math.round(referencePrice * (1 - pct) * 100) / 100;
  } else {
    // Short: stop-loss above entry
    orderBody.sl_trigger_price = Math.round(referencePrice * (1 + pct) * 100) / 100;
  }

  console.error(
    `AUTO STOP-LOSS: Set sl_trigger_price=${orderBody.sl_trigger_price} ` +
    `(${sl.default_percent}% from reference price ${referencePrice})`
  );
}

export { CONFIG, BASE_URL, SAFETY };
