#!/usr/bin/env node

const { resolveRuntimeDefaults } = require("./lib/ainft_config");

function parseArgs(argv) {
  const defaults = resolveRuntimeDefaults();
  const args = {
    baseUrl: defaults.baseUrl,
    apiKey: defaults.apiKey,
    timeoutMs: defaults.timeoutMs,
    configSource: defaults.configSource,
    procedure: "usage.points",
    format: "json",
  };

  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === "--base-url") {
      const raw = argv[i + 1];
      if (!raw) throw new Error("invalid --base-url <url>");
      args.baseUrl = raw.replace(/\/+$/, "");
      i += 1;
      continue;
    }
    if (token === "--api-key") {
      const raw = argv[i + 1];
      if (!raw) throw new Error("invalid --api-key <key>");
      args.apiKey = raw.trim();
      i += 1;
      continue;
    }
    if (token === "--timeout-ms") {
      const raw = argv[i + 1];
      if (!raw || !/^\d+$/.test(raw)) {
        throw new Error("invalid --timeout-ms <number>");
      }
      args.timeoutMs = Number(raw);
      i += 1;
      continue;
    }
    if (token === "--procedure") {
      const raw = argv[i + 1];
      if (!raw) throw new Error("invalid --procedure <router.procedure>");
      args.procedure = raw.trim();
      i += 1;
      continue;
    }
    if (token === "--format") {
      const raw = argv[i + 1];
      if (!raw || !["json", "text"].includes(raw)) {
        throw new Error("invalid --format <json|text>");
      }
      args.format = raw;
      i += 1;
      continue;
    }
    throw new Error(`unknown arg: ${token}`);
  }
  return args;
}

function buildBatchInput() {
  return {
    "0": {
      json: null,
      meta: { values: ["undefined"], v: 1 },
    },
  };
}

function extractTrpcData(body) {
  if (Array.isArray(body) && body[0]) {
    return body[0]?.result?.data?.json ?? body[0]?.result?.data ?? body[0];
  }
  return body?.result?.data?.json ?? body?.result?.data ?? body;
}

async function queryQuota(args) {
  if (!args.apiKey) {
    throw new Error("AINFT_API_KEY is required (--api-key, env, or ainft-config.json)");
  }

  const input = encodeURIComponent(JSON.stringify(buildBatchInput()));
  const url = `${args.baseUrl}/trpc/lambda/${args.procedure}?batch=1&input=${input}`;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), args.timeoutMs);
  try {
    const resp = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${args.apiKey}`,
      },
      signal: controller.signal,
    });

    const text = await resp.text();
    let body = {};
    try {
      body = text ? JSON.parse(text) : {};
    } catch {
      body = { raw: text };
    }

    return {
      http_status: resp.status,
      procedure: args.procedure,
      data: extractTrpcData(body),
      raw: body,
      ok: resp.ok,
    };
  } finally {
    clearTimeout(timer);
  }
}

function toText(result) {
  if (result.ok) {
    return `AINFT 额度查询成功 (${result.procedure})${result.config_source ? ` (config: ${result.config_source})` : ""}`;
  }
  return `AINFT 额度查询失败: http=${result.http_status}, procedure=${result.procedure}`;
}

async function main() {
  try {
    const args = parseArgs(process.argv.slice(2));
    const result = await queryQuota(args);
    if (!result.config_source && args.configSource) {
      result.config_source = args.configSource;
    }
    if (args.format === "text") {
      process.stdout.write(`${toText(result)}\n`);
      return;
    }
    process.stdout.write(`${JSON.stringify(result)}\n`);
  } catch (err) {
    process.stderr.write(
      `${JSON.stringify({
        error: err.message,
        usage:
          "node scripts/check_quota.js [--api-key <key>] [--base-url <url>] [--procedure usage.points] [--timeout-ms <ms>] [--format json|text]  # supports ainft-config.json",
      })}\n`,
    );
    process.exit(1);
  }
}

main().catch((err) => {
  process.stderr.write(`${JSON.stringify({ error: err.message })}\n`);
  process.exit(1);
});
