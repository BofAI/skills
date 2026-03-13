#!/usr/bin/env node
/**
 * search.js - Universal search across TronScan
 *
 * Usage:
 *   node scripts/search.js <term> [--type <type>] [--limit <n>]
 *
 * Types: token, address, contract, transaction, block (default: all)
 *
 * Examples:
 *   node scripts/search.js USDT
 *   node scripts/search.js TRX --type token
 *   node scripts/search.js TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t --type address
 */

const { apiGet, output, fatal, parseArgs, log } = require('./utils');

async function main() {
  const { args, positional } = parseArgs(process.argv);
  const term = positional[0];
  if (!term) fatal('Usage: node scripts/search.js <term> [--type <type>] [--limit <n>]');

  const params = {
    term,
    start: args.start || 0,
    limit: Math.min(Number(args.limit) || 20, 50),
  };
  if (args.type) params.type = args.type;

  log(`Searching for "${term}"...`);
  const data = await apiGet('search', params);
  output(data);
}

main().catch(e => fatal(e.message));
