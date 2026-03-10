#!/usr/bin/env node

const { getConfig } = require("./lib/ainft_config");

function parseArgs(argv) {
  const args = {
    page: 1,
    pageSize: 20,
    sortBy: "createdAt",
    order: "desc",
    format: "json",
  };
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
    if (token === "--page") {
      args.page = Number(next || "1");
      i += 1;
      continue;
    }
    if (token === "--page-size") {
      args.pageSize = Number(next || "20");
      i += 1;
      continue;
    }
    if (token === "--sort-by") {
      args.sortBy = next || "createdAt";
      i += 1;
      continue;
    }
    if (token === "--order") {
      args.order = next || "desc";
      i += 1;
      continue;
    }
    if (token === "--format") {
      args.format = next || "json";
      i += 1;
      continue;
    }
    throw new Error(`unknown arg: ${token}`);
  }
  return args;
}

function buildInput(args) {
  return encodeURIComponent(
    JSON.stringify({
      0: {
        json: {
          page: args.page,
          pageSize: args.pageSize,
          sortBy: args.sortBy,
          order: args.order,
        },
      },
    }),
  );
}

function normalizeOrdersPayload(raw) {
  const item = Array.isArray(raw) ? raw[0] : raw;
  const payload = item && item.result && item.result.data ? item.result.data : null;
  const resolved = payload && payload.json ? payload.json : payload;
  if (!resolved || typeof resolved !== "object") {
    return {
      procedure: "order.listOrders",
      orders: [],
      page: null,
      page_size: null,
      total: null,
      raw: resolved,
    };
  }
  const orders = Array.isArray(resolved.data)
    ? resolved.data
    : Array.isArray(resolved.orders)
      ? resolved.orders
      : [];
  return {
    procedure: "order.listOrders",
    orders,
    page: resolved.page ?? null,
    page_size: resolved.pageSize ?? null,
    total: resolved.total ?? orders.length,
    raw: resolved,
  };
}

async function main() {
  try {
    const args = parseArgs(process.argv.slice(2));
    const config = getConfig(args);
    if (!config.apiKey) {
      throw new Error("missing AINFT_API_KEY or ainft-config.json api_key");
    }

    const url = `${config.baseUrl}/trpc/lambda/order.listOrders?batch=1&input=${buildInput(args)}`;
    const response = await fetch(url, {
      headers: {
        Accept: "*/*",
        Authorization: `Bearer ${config.apiKey}`,
      },
    });
    const text = await response.text();
    const data = text ? JSON.parse(text) : null;
    const normalized = normalizeOrdersPayload(data);
    const result = {
      ok: response.ok,
      type: "orders",
      summary: `Fetched ${normalized.orders.length} orders`,
      procedure: normalized.procedure,
      http_status: response.status,
      page: normalized.page,
      page_size: normalized.page_size,
      total: normalized.total,
      orders: normalized.orders,
      data: normalized.raw,
      config_path: config.configPath,
    };

    if (args.format === "text") {
      process.stdout.write(`${result.summary}\n`);
      return;
    }
    process.stdout.write(`${JSON.stringify(result)}\n`);
  } catch (err) {
    process.stderr.write(
      `${JSON.stringify({
        error: err.message,
        usage: "node scripts/check_orders.js [--page <n>] [--page-size <n>] [--format json|text]",
      })}\n`,
    );
    process.exit(1);
  }
}

main();
