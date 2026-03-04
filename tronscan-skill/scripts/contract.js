#!/usr/bin/env node
/**
 * contract.js - Smart contract details and analytics
 *
 * Usage:
 *   node scripts/contract.js <address>                         # Contract detail
 *   node scripts/contract.js --list [--search <term>]          # Contract list / search
 *   node scripts/contract.js <address> --energy                # Energy consumption stats
 *   node scripts/contract.js <address> --calls                 # Top call statistics
 *   node scripts/contract.js <address> --callers [--day <ts>]  # All callers
 *   node scripts/contract.js <address> --analysis --type <0-5> # Daily analytics
 *
 * Analysis types: 0=callers, 1=calls, 2=energy, 3=bandwidth, 4=trx_transfers, 5=token_transfers
 *
 * Examples:
 *   node scripts/contract.js TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t
 *   node scripts/contract.js --list --search "USDT" --limit 10
 *   node scripts/contract.js TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t --energy
 */

const { apiGet, output, fatal, parseArgs, log } = require('./utils');

async function main() {
  const { args, positional } = parseArgs(process.argv);

  if (args.list) {
    log('Fetching contract list...');
    const params = {
      sort: args.sort || '-trxCount',
      start: args.start || 0,
      limit: Math.min(Number(args.limit) || 20, 200),
    };
    if (args.search) params.search = args.search;
    if (args['open-source-only']) params['open-source-only'] = 1;
    if (args['verified-only']) params['verified-only'] = 1;
    const data = await apiGet('contracts', params);
    output(data);
    return;
  }

  const address = positional[0];
  if (!address) fatal('Usage: node scripts/contract.js <address> [--energy] [--calls] [--callers] [--analysis] OR --list');

  if (args.energy) {
    log(`Fetching energy stats for ${address}...`);
    const data = await apiGet('contractEnergy', { address });
    output(data);
    return;
  }

  if (args.calls) {
    log(`Fetching top call stats for ${address}...`);
    const data = await apiGet('contractTopCall', { contract_address: address });
    output(data);
    return;
  }

  if (args.callers) {
    log(`Fetching callers for ${address}...`);
    const params = { address };
    if (args.day) params.day = args.day;
    const data = await apiGet('contractCallers', params);
    output(data);
    return;
  }

  if (args.analysis) {
    log(`Fetching contract analytics for ${address}...`);
    const params = { address, type: args.type || 0 };
    if (args.start_timestamp) params.start_timestamp = args.start_timestamp;
    if (args.end_timestamp) params.end_timestamp = args.end_timestamp;
    const data = await apiGet('contractAnalysis', params);
    output(data);
    return;
  }

  log(`Fetching contract detail for ${address}...`);
  const data = await apiGet('contract', { contract: address });
  output(data);
}

main().catch(e => fatal(e.message));
