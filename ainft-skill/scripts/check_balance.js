#!/usr/bin/env node

const { getConfig } = require("./lib/ainft_config");

function parseArgs(argv) {
  const args = { format: "json" };
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    const next = argv[i + 1];
    if (token === "--api-key") {
      args.apiKey = next || "";
      i += 1;
      continue;
    }
    if (token === "--base-url") {
      args.baseUrl = next || "";
      i += 1;
      continue;
    }
    if (token === "--format") {
      if (!next || !["json", "text"].includes(next)) {
        throw new Error("invalid --format <json|text>");
      }
      args.format = next;
      i += 1;
      continue;
    }
    throw new Error(`unknown arg: ${token}`);
  }
  return args;
}

async function fetchJson(url, options, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    const text = await response.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (_) {
      data = { raw: text };
    }
    return { ok: response.ok, status: response.status, data };
  } finally {
    clearTimeout(timer);
  }
}

function trpcInput() {
  return encodeURIComponent(
    JSON.stringify({
      0: {
        json: null,
        meta: { values: ["undefined"], v: 1 },
      },
    }),
  );
}

async function queryUserBalance(config) {
  if (!config.apiKey) {
    throw new Error("missing AINFT_API_KEY or ainft-config.json api_key");
  }
  const url = `${config.baseUrl}/trpc/lambda/usage.points?batch=1&input=${trpcInput()}`;
  return fetchJson(
    url,
    {
      headers: {
        Accept: "*/*",
        Authorization: `Bearer ${config.apiKey}`,
      },
    },
    config.timeoutMs,
  );
}

function normalizeResult(config, userResult) {
  if (userResult && userResult.ok) {
    const item = Array.isArray(userResult.data) ? userResult.data[0] : userResult.data;
    const payload = item && item.result && item.result.data ? item.result.data : {};
    const resolved = payload && payload.json ? payload.json : payload;
    const pointsBalance = resolved.points_balance;
    return {
      ok: true,
      type: "user_points_balance",
      summary: `AINFT points balance: ${pointsBalance}`,
      points_balance: pointsBalance,
      unit: "points",
      http_status: userResult.status,
      config_path: config.configPath,
    };
  }

  return {
    ok: false,
    type: "balance_query_failed",
    summary: "Failed to query AINFT balance",
    user_result: userResult,
    config_path: config.configPath,
  };
}

async function main() {
  try {
    const args = parseArgs(process.argv.slice(2));
    const config = getConfig(args);
    const userResult = await queryUserBalance(config);
    const result = normalizeResult(config, userResult);

    if (args.format === "text") {
      if (!result.ok) {
        throw new Error("balance query failed");
      }
      process.stdout.write(`${result.summary}\n`);
      return;
    }
    process.stdout.write(`${JSON.stringify(result)}\n`);
  } catch (err) {
    process.stderr.write(
      `${JSON.stringify({
        error: err.message,
        usage: "node scripts/check_balance.js [--format json|text]",
      })}\n`,
    );
    process.exit(1);
  }
}

main();
