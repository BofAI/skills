#!/usr/bin/env node
/**
 * block.js - Block information
 *
 * Usage:
 *   node scripts/block.js                                     # Latest block
 *   node scripts/block.js <number>                            # Specific block by number
 *   node scripts/block.js --list [--limit <n>]                # Recent blocks
 *   node scripts/block.js --producer <address>                # Blocks by producer
 *   node scripts/block.js --stats                             # Block statistics
 *
 * Examples:
 *   node scripts/block.js
 *   node scripts/block.js 50000000
 *   node scripts/block.js --list --limit 10
 *   node scripts/block.js --stats
 */

const { apiGet, output, fatal, parseArgs, log } = require('./utils');

async function main() {
  const { args, positional } = parseArgs(process.argv);

  if (args.stats) {
    log('Fetching block statistics...');
    const data = await apiGet('blockStats');
    output(data);
    return;
  }

  const params = {
    sort: args.sort || '-number',
    start: args.start || 0,
    limit: Math.min(Number(args.limit) || 1, 200),
  };

  if (args.list) {
    params.limit = Math.min(Number(args.limit) || 20, 200);
  }

  if (args.producer) {
    params.producer = typeof args.producer === 'string' ? args.producer : undefined;
  }

  if (args.start_timestamp) params.start_timestamp = args.start_timestamp;
  if (args.end_timestamp) params.end_timestamp = args.end_timestamp;

  const blockNum = positional[0];
  if (blockNum) {
    // To get a specific block, we use start=blockNum-1, limit=1 with sort
    // Actually the API supports filtering by number via the block list endpoint
    params.limit = 1;
    params.number = blockNum;
  }

  log('Fetching block data...');
  const data = await apiGet('block', params);
  output(data);
}

main().catch(e => fatal(e.message));
