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

export { CONFIG, BASE_URL };
