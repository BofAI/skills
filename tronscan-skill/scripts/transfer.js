#!/usr/bin/env node
/**
 * transfer.js - Transfer history for TRX, TRC10, and TRC20 tokens
 *
 * Usage:
 *   node scripts/transfer.js --trx <address>                             # TRX transfers
 *   node scripts/transfer.js --trc20 <address> [--token <contract>]      # TRC20 transfers
 *   node scripts/transfer.js --trc10 <address> [--token <token_id>]      # TRC10 transfers
 *   node scripts/transfer.js --trc20-contract <contract> [--addr <addr>] # TRC20 transfers by contract
 *   node scripts/transfer.js --internal <address>                        # Internal transactions
 *
 * Common options:
 *   --direction <0|1|2>     0=all, 1=in, 2=out (TRX/TRC20/TRC10)
 *   --start_timestamp <ms>  Start time filter
 *   --end_timestamp <ms>    End time filter
 *   --limit <n>             Results per page (default: 20, max: 200)
 *   --start <n>             Offset for pagination
 *
 * Examples:
 *   node scripts/transfer.js --trx TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf --limit 10
 *   node scripts/transfer.js --trc20 TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf --direction 2
 *   node scripts/transfer.js --trc20-contract TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t --limit 20
 */

const { apiGet, output, fatal, parseArgs, log } = require('./utils');

async function main() {
  const { args, positional } = parseArgs(process.argv);

  const commonParams = {
    start: args.start || 0,
    limit: Math.min(Number(args.limit) || 20, 200),
  };
  if (args.direction) commonParams.direction = args.direction;
  if (args.start_timestamp) commonParams.start_timestamp = args.start_timestamp;
  if (args.end_timestamp) commonParams.end_timestamp = args.end_timestamp;

  if (args.trx) {
    const address = typeof args.trx === 'string' ? args.trx : positional[0];
    if (!address) fatal('--trx requires an address');
    log(`Fetching TRX transfers for ${address}...`);
    const data = await apiGet('transferTrx', { ...commonParams, address });
    output(data);
    return;
  }

  if (args.trc20) {
    const address = typeof args.trc20 === 'string' ? args.trc20 : positional[0];
    if (!address) fatal('--trc20 requires an address');
    log(`Fetching TRC20 transfers for ${address}...`);
    const params = { ...commonParams, address };
    if (args.token) params.trc20Id = args.token;
    const data = await apiGet('transferTrc20', params);
    output(data);
    return;
  }

  if (args.trc10) {
    const address = typeof args.trc10 === 'string' ? args.trc10 : positional[0];
    if (!address) fatal('--trc10 requires an address');
    log(`Fetching TRC10 transfers for ${address}...`);
    const params = { ...commonParams, address };
    if (args.token) params.trc10Id = args.token;
    const data = await apiGet('transferTrc10', params);
    output(data);
    return;
  }

  if (args['trc20-contract']) {
    const contract = typeof args['trc20-contract'] === 'string' ? args['trc20-contract'] : positional[0];
    if (!contract) fatal('--trc20-contract requires a contract address');
    log(`Fetching TRC20 transfers for contract ${contract}...`);
    const params = { ...commonParams, contract_address: contract };
    if (args.addr) params.relatedAddress = args.addr;
    if (args.from) params.fromAddress = args.from;
    if (args.to) params.toAddress = args.to;
    const data = await apiGet('trc20Transfers', params);
    output(data);
    return;
  }

  if (args.internal) {
    const address = typeof args.internal === 'string' ? args.internal : positional[0];
    if (!address) fatal('--internal requires an address');
    log(`Fetching internal transactions for ${address}...`);
    const data = await apiGet('internalTransaction', { ...commonParams, address });
    output(data);
    return;
  }

  fatal('Usage: node scripts/transfer.js --trx <addr> | --trc20 <addr> | --trc10 <addr> | --trc20-contract <contract> | --internal <addr>');
}

main().catch(e => fatal(e.message));
