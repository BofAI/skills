#!/usr/bin/env node
/**
 * transaction.js - Transaction lookup and history
 *
 * Usage:
 *   node scripts/transaction.js <hash>                                  # Single transaction by hash
 *   node scripts/transaction.js --list [--from <addr>] [--to <addr>]    # Transaction list
 *   node scripts/transaction.js --stats                                 # Transaction statistics
 *
 * List options:
 *   --from <address>         Filter by sender
 *   --to <address>           Filter by receiver
 *   --block <number>         Filter by block number
 *   --start_timestamp <ms>   Start time filter (milliseconds)
 *   --end_timestamp <ms>     End time filter (milliseconds)
 *   --sort <field>           Sort field (default: -timestamp)
 *   --limit <n>              Results per page (default: 20, max: 200)
 *   --start <n>              Offset for pagination
 *
 * Examples:
 *   node scripts/transaction.js abc123def456...
 *   node scripts/transaction.js --list --from TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf --limit 10
 *   node scripts/transaction.js --stats
 */

const { apiGet, output, fatal, parseArgs, log } = require('./utils');

async function main() {
  const { args, positional } = parseArgs(process.argv);

  if (args.stats) {
    log('Fetching transaction statistics...');
    const data = await apiGet('transactionStats');
    output(data);
    return;
  }

  if (args.list) {
    log('Fetching transaction list...');
    const params = {
      sort: args.sort || '-timestamp',
      start: args.start || 0,
      limit: Math.min(Number(args.limit) || 20, 200),
    };
    if (args.from) params.fromAddress = args.from;
    if (args.to) params.toAddress = args.to;
    if (args.block) params.block = args.block;
    if (args.start_timestamp) params.start_timestamp = args.start_timestamp;
    if (args.end_timestamp) params.end_timestamp = args.end_timestamp;
    if (args.type) params.type = args.type;
    const data = await apiGet('transaction', params);
    output(data);
    return;
  }

  const hash = positional[0];
  if (!hash) fatal('Usage: node scripts/transaction.js <hash> OR --list OR --stats');

  log(`Fetching transaction ${hash}...`);
  const data = await apiGet('transactionInfo', { hash });
  output(data);
}

main().catch(e => fatal(e.message));
