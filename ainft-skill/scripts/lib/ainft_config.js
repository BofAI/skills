const fs = require("fs");
const os = require("os");
const path = require("path");

const DEFAULT_BASE_URL = "https://chat-dev.ainft.com";
const DEFAULT_TIMEOUT_MS = 15000;

function readJson(filePath) {
  if (!fs.existsSync(filePath)) return null;
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function loadAinftConfig() {
  const configFiles = [
    path.join(process.cwd(), "ainft-config.json"),
    path.join(os.homedir(), ".ainft", "config.json"),
    path.join(os.homedir(), ".mcporter", "ainft-config.json"),
  ];

  for (const filePath of configFiles) {
    const config = readJson(filePath);
    if (config && typeof config === "object") {
      return { config, source: filePath };
    }
  }
  return { config: {}, source: "" };
}

function normalizeNumber(value, fallback) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && /^\d+$/.test(value)) return Number(value);
  return fallback;
}

function resolveRuntimeDefaults() {
  const { config, source } = loadAinftConfig();
  const baseUrl = (process.env.AINFT_BASE_URL || config.base_url || DEFAULT_BASE_URL).replace(/\/+$/, "");
  const apiKey = process.env.AINFT_API_KEY || config.api_key || "";
  const timeoutMs = normalizeNumber(process.env.AINFT_TIMEOUT_MS || config.timeout_ms, DEFAULT_TIMEOUT_MS);

  return {
    baseUrl,
    apiKey,
    timeoutMs,
    configSource: source,
  };
}

module.exports = {
  resolveRuntimeDefaults,
};
