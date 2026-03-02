#!/usr/bin/env node

const fs = require("fs");
const os = require("os");
const path = require("path");

const DEFAULT_MCP_URL = process.env.AINFT_MCP_URL || "http://127.0.0.1:8000/mcp";
const DEFAULT_TRON_RPC = process.env.AINFT_TRON_RPC_URL || "https://nile.trongrid.io";
const DEFAULT_TIMEOUT_MS = Number(process.env.AINFT_TIMEOUT_MS || 20000);

function parseArgs(argv) {
  const args = {
    amount: "",
    mcpUrl: DEFAULT_MCP_URL,
    tronRpcUrl: DEFAULT_TRON_RPC,
    privateKey: "",
    timeoutMs: DEFAULT_TIMEOUT_MS,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === "--amount") {
      const raw = argv[i + 1];
      if (!raw) throw new Error("invalid --amount <value>");
      args.amount = raw.trim();
      i += 1;
      continue;
    }
    if (token === "--mcp-url") {
      const raw = argv[i + 1];
      if (!raw) throw new Error("invalid --mcp-url <url>");
      args.mcpUrl = raw.trim();
      i += 1;
      continue;
    }
    if (token === "--tron-rpc") {
      const raw = argv[i + 1];
      if (!raw) throw new Error("invalid --tron-rpc <url>");
      args.tronRpcUrl = raw.trim();
      i += 1;
      continue;
    }
    if (token === "--private-key") {
      const raw = argv[i + 1];
      if (!raw) throw new Error("invalid --private-key <key>");
      args.privateKey = raw.trim();
      i += 1;
      continue;
    }
    if (token === "--timeout-ms") {
      const raw = argv[i + 1];
      if (!raw || !/^\d+$/.test(raw)) throw new Error("invalid --timeout-ms <ms>");
      args.timeoutMs = Number(raw);
      i += 1;
      continue;
    }
    throw new Error(`unknown arg: ${token}`);
  }

  if (!args.amount) throw new Error("missing --amount");
  return args;
}

function extractSseJson(raw) {
  const lines = String(raw).split("\n");
  for (const line of lines) {
    const t = line.trim();
    if (!t.startsWith("data: ")) continue;
    const payload = t.slice("data: ".length).trim();
    if (!payload) continue;
    try {
      return JSON.parse(payload);
    } catch {
      // continue
    }
  }
  throw new Error("failed to parse MCP SSE data payload");
}

async function postMcpToolCall(mcpUrl, toolName, argumentsObj, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const reqBody = {
      jsonrpc: "2.0",
      id: `${toolName}-${Date.now()}`,
      method: "tools/call",
      params: { name: toolName, arguments: argumentsObj },
    };
    const resp = await fetch(mcpUrl, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        accept: "application/json, text/event-stream",
      },
      body: JSON.stringify(reqBody),
      signal: controller.signal,
    });
    const raw = await resp.text();
    if (!resp.ok) {
      throw new Error(`mcp http error: ${resp.status}, body=${raw.slice(0, 500)}`);
    }
    return extractSseJson(raw);
  } finally {
    clearTimeout(timer);
  }
}

function getStructuredContent(rpcResponse) {
  const result = rpcResponse?.result || {};
  if (result.structuredContent) return result.structuredContent;
  const first = result?.content?.[0]?.text;
  if (!first) return {};
  try {
    return JSON.parse(first);
  } catch {
    return {};
  }
}

function loadTronWeb() {
  const candidatePaths = [
    process.cwd(),
    __dirname,
    path.resolve(__dirname, "..", "..", "x402-payment"),
  ];
  for (const p of candidatePaths) {
    try {
      const resolved = require.resolve("tronweb", { paths: [p] });
      // eslint-disable-next-line global-require, import/no-dynamic-require
      const mod = require(resolved);
      return mod.TronWeb || mod.default?.TronWeb || mod.default || mod;
    } catch {
      // try next path
    }
  }
  throw new Error(
    "tronweb dependency not found. Install it in ainft-skill or ensure ../x402-payment/node_modules is available."
  );
}

function findPrivateKey() {
  if (process.env.TRON_PRIVATE_KEY) return process.env.TRON_PRIVATE_KEY;
  if (process.env.PRIVATE_KEY) return process.env.PRIVATE_KEY;

  const cfgFiles = [
    path.join(process.cwd(), "x402-config.json"),
    path.join(os.homedir(), ".x402-config.json"),
  ];
  for (const f of cfgFiles) {
    if (!fs.existsSync(f)) continue;
    try {
      const cfg = JSON.parse(fs.readFileSync(f, "utf8"));
      if (cfg.tron_private_key) return cfg.tron_private_key;
      if (cfg.private_key) return cfg.private_key;
    } catch {
      // ignore
    }
  }

  const mcporter = path.join(os.homedir(), ".mcporter", "mcporter.json");
  if (fs.existsSync(mcporter)) {
    try {
      const cfg = JSON.parse(fs.readFileSync(mcporter, "utf8"));
      const servers = cfg.mcpServers || {};
      for (const k of Object.keys(servers)) {
        const env = servers[k]?.env || {};
        if (env.TRON_PRIVATE_KEY) return env.TRON_PRIVATE_KEY;
        if (env.PRIVATE_KEY) return env.PRIVATE_KEY;
      }
    } catch {
      // ignore
    }
  }
  return "";
}

async function sendNativeTrx({ tronRpcUrl, privateKey, to, amountSun }) {
  const TronWeb = loadTronWeb();

  const tronWeb = new TronWeb({ fullHost: tronRpcUrl, privateKey });
  const tx = await tronWeb.trx.sendTransaction(to, amountSun);
  if (!tx?.txid) {
    throw new Error(`sendTransaction failed: ${JSON.stringify(tx || {})}`);
  }
  return tx.txid;
}

async function main() {
  try {
    const args = parseArgs(process.argv.slice(2));
    const resolvedPrivateKey = (args.privateKey || findPrivateKey()).trim();
    if (!resolvedPrivateKey) {
      throw new Error(
        "TRON private key not found. Set TRON_PRIVATE_KEY or provide x402-config.json / ~/.x402-config.json / ~/.mcporter/mcporter.json"
      );
    }

    const step1Rpc = await postMcpToolCall(
      args.mcpUrl,
      "ainft_pay_trx",
      { amount: args.amount },
      args.timeoutMs
    );
    const step1 = getStructuredContent(step1Rpc);
    if (step1.status !== "payment_required_native") {
      throw new Error(`unexpected step1 status: ${step1.status || "unknown"}`);
    }

    const to = step1?.transfer?.to;
    const amountSun = Number(step1?.transfer?.amount_sun);
    if (!to || !Number.isFinite(amountSun)) {
      throw new Error("invalid transfer instructions from ainft_pay_trx");
    }

    const txid = await sendNativeTrx({
      tronRpcUrl: args.tronRpcUrl,
      privateKey: resolvedPrivateKey,
      to,
      amountSun,
    });

    const step2Rpc = await postMcpToolCall(
      args.mcpUrl,
      "ainft_pay_trx",
      { amount: args.amount, txid },
      args.timeoutMs + 20000
    );
    const step2 = getStructuredContent(step2Rpc);

    process.stdout.write(
      `${JSON.stringify(
        {
          mode: "trx_native",
          step1,
          txid,
          step2,
        },
        null,
        2
      )}\n`
    );
  } catch (err) {
    process.stderr.write(
      `${JSON.stringify(
        {
          error: err.message,
          usage:
            "node scripts/pay_trx_native.js --amount 1 [--mcp-url <url>] [--tron-rpc <url>] [--timeout-ms 20000]",
        },
        null,
        2
      )}\n`
    );
    process.exit(1);
  }
}

main();
