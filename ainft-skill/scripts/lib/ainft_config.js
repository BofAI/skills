#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const os = require("os");

function loadJson(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      return null;
    }
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (_) {
    return null;
  }
}

function candidatePaths() {
  return [
    path.resolve(process.cwd(), "ainft-config.json"),
    path.join(os.homedir(), ".ainft", "config.json"),
    path.join(os.homedir(), ".mcporter", "ainft-config.json"),
  ];
}

function readConfig() {
  for (const filePath of candidatePaths()) {
    const data = loadJson(filePath);
    if (data && typeof data === "object") {
      return { path: filePath, data };
    }
  }
  return { path: "", data: {} };
}

function getConfig(overrides = {}) {
  const loaded = readConfig();
  const data = loaded.data || {};
  return {
    configPath: loaded.path,
    apiKey: overrides.apiKey || process.env.AINFT_API_KEY || data.api_key || "",
    baseUrl: (overrides.baseUrl || process.env.AINFT_BASE_URL || data.base_url || "https://chat.ainft.com").replace(/\/+$/, ""),
    timeoutMs: Number(overrides.timeoutMs || process.env.AINFT_TIMEOUT_MS || data.timeout_ms || 15000),
  };
}

module.exports = {
  getConfig,
};
