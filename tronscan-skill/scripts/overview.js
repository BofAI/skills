#!/usr/bin/env node
/**
 * overview.js - TRON chain overview and statistics
 *
 * Usage:
 *   node scripts/overview.js                         # Full chain overview (homepage bundle)
 *   node scripts/overview.js --tps                   # Current TPS
 *   node scripts/overview.js --witnesses              # Super Representative list
 *   node scripts/overview.js --params                 # Chain parameters
 *   node scripts/overview.js --proposals              # Governance proposals
 *   node scripts/overview.js --daily-accounts [days]  # Daily new account stats
 *   node scripts/overview.js --funds                  # TRX funds & supply info
 *   node scripts/overview.js --trx-volume             # TRX historical price/volume
 *   node scripts/overview.js --nodes                  # Node map info
 *
 * Examples:
 *   node scripts/overview.js
 *   node scripts/overview.js --witnesses --limit 27
 *   node scripts/overview.js --daily-accounts 30
 *   node scripts/overview.js --trx-volume --source coingecko --limit 30
 */

const { apiGet, output, fatal, parseArgs, log } = require('./utils');

async function main() {
  const { args, positional } = parseArgs(process.argv);

  if (args.tps) {
    log('Fetching current TPS...');
    const data = await apiGet('tps');
    output(data);
    return;
  }

  if (args.witnesses) {
    log('Fetching witness list...');
    const params = {
      limit: Math.min(Number(args.limit) || 50, 200),
    };
    if (args.witnesstype) params.witnesstype = args.witnesstype;
    const data = await apiGet('witnesses', params);
    output(data);
    return;
  }

  if (args.params) {
    log('Fetching chain parameters...');
    const data = await apiGet('chainParams');
    output(data);
    return;
  }

  if (args.proposals) {
    log('Fetching proposals...');
    const params = {
      start: args.start || 0,
      limit: Math.min(Number(args.limit) || 20, 200),
    };
    if (args.sort) params.sort = args.sort;
    const data = await apiGet('proposals', params);
    output(data);
    return;
  }

  if (args['daily-accounts'] !== undefined) {
    const days = typeof args['daily-accounts'] === 'string'
      ? Number(args['daily-accounts'])
      : (positional[0] ? Number(positional[0]) : 15);
    log(`Fetching daily new accounts (${days} days)...`);
    const data = await apiGet('dailyAccounts', { days: Math.min(days, 2000) });
    output(data);
    return;
  }

  if (args.funds) {
    log('Fetching TRX funds/supply...');
    const data = await apiGet('funds');
    output(data);
    return;
  }

  if (args['trx-volume']) {
    log('Fetching TRX volume/price history...');
    const params = {
      limit: Math.min(Number(args.limit) || 30, 200),
    };
    if (args.source) params.source = args.source;
    if (args.start_timestamp) params.start_timestamp = args.start_timestamp;
    if (args.end_timestamp) params.end_timestamp = args.end_timestamp;
    const data = await apiGet('trxVolume', params);
    output(data);
    return;
  }

  if (args.nodes) {
    log('Fetching node map...');
    const data = await apiGet('nodemap');
    output(data);
    return;
  }

  // Default: full homepage bundle
  log('Fetching chain overview...');
  const data = await apiGet('homepage');
  output(data);
}

main().catch(e => fatal(e.message));
