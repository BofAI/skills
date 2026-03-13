#!/usr/bin/env node
/**
 * token.js - Token information, pricing, and holders
 *
 * Usage:
 *   node scripts/token.js --list [--filter <type>] [--sort <field>]   # Token overview list
 *   node scripts/token.js --trc20 <contract_address>                  # TRC20 token detail
 *   node scripts/token.js --trc10 <token_id>                          # TRC10 token detail
 *   node scripts/token.js --price [token_symbol]                      # Token price (default: trx)
 *   node scripts/token.js --holders <contract_address>                # Token holder list
 *   node scripts/token.js --supply <contract_address>                 # TRC20 total supply
 *   node scripts/token.js --distribution <token_id>                   # Holdings distribution
 *
 * List filters: trc10, trc20, trc721, trc1155, all, top
 * List sort fields: priceInTrx, gain, volume24hInTrx, holderCount, marketcap
 *
 * Examples:
 *   node scripts/token.js --list --filter trc20 --sort marketcap --limit 10
 *   node scripts/token.js --trc20 TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t
 *   node scripts/token.js --price trx
 *   node scripts/token.js --holders TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t --limit 20
 */

const { apiGet, output, fatal, parseArgs, log, resolveToken } = require('./utils');

async function main() {
  const { args, positional } = parseArgs(process.argv);

  if (args.list) {
    log('Fetching token overview...');
    const params = {
      start: args.start || 0,
      limit: Math.min(Number(args.limit) || 20, 500),
    };
    if (args.filter) params.filter = args.filter;
    if (args.sort) params.sort = args.sort;
    if (args.order) params.order = args.order;
    const data = await apiGet('tokensOverview', params);
    output(data);
    return;
  }

  if (args.trc20) {
    const contract = typeof args.trc20 === 'string' ? args.trc20 : positional[0];
    if (!contract) fatal('--trc20 requires a contract address');
    log(`Fetching TRC20 token detail for ${contract}...`);
    const data = await apiGet('tokenTrc20', { contract });
    output(data);
    return;
  }

  if (args.trc10) {
    const id = typeof args.trc10 === 'string' ? args.trc10 : positional[0];
    if (!id) fatal('--trc10 requires a token ID');
    log(`Fetching TRC10 token detail for ID ${id}...`);
    const data = await apiGet('tokenTrc10', { id });
    output(data);
    return;
  }

  if (args.price !== undefined) {
    const symbol = (typeof args.price === 'string' ? args.price : positional[0]) || 'trx';
    log(`Fetching price for ${symbol}...`);
    const data = await apiGet('tokenPrice', { token: symbol.toLowerCase() });
    output(data);
    return;
  }

  if (args.holders) {
    const contract = typeof args.holders === 'string' ? args.holders : positional[0];
    if (!contract) fatal('--holders requires a contract address');
    log(`Fetching holders for ${contract}...`);
    const params = {
      contract_address: contract,
      start: args.start || 0,
      limit: Math.min(Number(args.limit) || 20, 200),
    };
    if (args.holder_address) params.holder_address = args.holder_address;
    const data = await apiGet('tokenHoldersTrc20', params);
    output(data);
    return;
  }

  if (args.supply) {
    const address = typeof args.supply === 'string' ? args.supply : positional[0];
    if (!address) fatal('--supply requires a contract address');
    log(`Fetching total supply for ${address}...`);
    const data = await apiGet('tokenTotalSupply', { address });
    output(data);
    return;
  }

  if (args.distribution) {
    const tokenId = typeof args.distribution === 'string' ? args.distribution : positional[0];
    if (!tokenId) fatal('--distribution requires a token ID');
    log(`Fetching distribution for token ${tokenId}...`);
    const data = await apiGet('tokenDistribution', { tokenId });
    output(data);
    return;
  }

  fatal('Usage: node scripts/token.js --list | --trc20 <addr> | --trc10 <id> | --price [sym] | --holders <addr> | --supply <addr> | --distribution <id>');
}

main().catch(e => fatal(e.message));
