#!/usr/bin/env node
/**
 * account.js - Account details, balances, and token holdings
 *
 * Usage:
 *   node scripts/account.js <address>                          # Account details
 *   node scripts/account.js <address> --tokens                 # Token holdings
 *   node scripts/account.js <address> --wallet                 # Full wallet portfolio with USD values
 *   node scripts/account.js <address> --resources              # Bandwidth & energy resources
 *   node scripts/account.js <address> --analysis --type <0-4>  # Daily analytics
 *
 * Analysis types: 0=balance, 1=transfers, 2=energy, 3=bandwidth, 4=transactions
 *
 * Examples:
 *   node scripts/account.js TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf
 *   node scripts/account.js TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf --tokens --limit 50
 *   node scripts/account.js TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf --wallet
 */

const { apiGet, output, fatal, parseArgs, log } = require('./utils');

async function main() {
  const { args, positional } = parseArgs(process.argv);
  const address = positional[0];
  if (!address) fatal('Usage: node scripts/account.js <address> [--tokens] [--wallet] [--resources] [--analysis]');

  if (args.tokens) {
    log(`Fetching token holdings for ${address}...`);
    const data = await apiGet('accountTokens', {
      address,
      start: args.start || 0,
      limit: Math.min(Number(args.limit) || 20, 200),
      show: args.show || 0,
    });
    output(data);
  } else if (args.wallet) {
    log(`Fetching wallet portfolio for ${address}...`);
    const data = await apiGet('accountWallet', {
      address,
      asset_type: args.asset_type || 0,
    });
    output(data);
  } else if (args.resources) {
    log(`Fetching resources for ${address}...`);
    const data = await apiGet('accountResource', {
      address,
      type: args.type || undefined,
      resourceType: args.resourceType || undefined,
    });
    output(data);
  } else if (args.analysis) {
    log(`Fetching daily analytics for ${address}...`);
    const params = { address, type: args.type || 0 };
    if (args.start_timestamp) params.start_timestamp = args.start_timestamp;
    if (args.end_timestamp) params.end_timestamp = args.end_timestamp;
    const data = await apiGet('accountAnalysis', params);
    output(data);
  } else {
    log(`Fetching account details for ${address}...`);
    const data = await apiGet('account', { address });
    output(data);
  }
}

main().catch(e => fatal(e.message));
