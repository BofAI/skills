#!/usr/bin/env node

/**
 * Sun Token Price Script
 *
 * Fetch token price from Sun Open API:
 *   https://open.sun.io/apiv2/price?tokenAddress=<TOKEN_ADDRESS>
 *
 * Usage:
 *   node price.js <TOKEN_SYMBOL_OR_ADDRESS> [--currency USD]
 *
 * Examples:
 *   node price.js TRX
 *   node price.js T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb
 *   node price.js USDT --currency USD
 */

const axios = require('axios');
const path = require('path');
const fs = require('fs');

// Load token addresses (for symbol → address resolution, mainnet only)
const tokensPath = path.join(__dirname, '../resources/common_tokens.json');
const tokens = JSON.parse(fs.readFileSync(tokensPath, 'utf8'));

const PRICE_API = 'https://open.sun.io/apiv2/price';

function parseArgs() {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.error('Usage: node price.js <TOKEN_SYMBOL_OR_ADDRESS> [--currency USD]');
    console.error('');
    console.error('TOKEN_SYMBOL_OR_ADDRESS can be token symbol (TRX, USDT) or TRC20 address (T9yD...)');
    process.exit(1);
  }

  let tokenInput = null;
  let currency = 'USD';

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--currency' && i + 1 < args.length) {
      currency = args[i + 1].toUpperCase();
      i++;
    } else if (!tokenInput) {
      // Don't uppercase if it's an address (starts with T and length 34)
      tokenInput =
        args[i].startsWith('T') && args[i].length === 34
          ? args[i]
          : args[i].toUpperCase();
    }
  }

  return { tokenInput, currency };
}

function resolveTokenAddress(tokenInput) {
  // If it's already an address (starts with T and 34 chars), return directly
  if (tokenInput.startsWith('T') && tokenInput.length === 34) {
    return { tokenAddress: tokenInput, tokenSymbol: null };
  }

  const mainnetTokens = tokens.mainnet;
  if (!mainnetTokens) {
    throw new Error('Mainnet token list not found in resources/common_tokens.json');
  }

  const token = mainnetTokens[tokenInput];
  if (!token) {
    throw new Error(`Unknown token symbol on mainnet: ${tokenInput}`);
  }

  return { tokenAddress: token.address, tokenSymbol: tokenInput };
}

async function getTokenPrice(tokenAddress, currency = 'USD') {
  const url = `${PRICE_API}?tokenAddress=${encodeURIComponent(tokenAddress)}`;

  try {
    const response = await axios.get(url, { timeout: 10000 });
    const body = response.data;

    if (body.code !== 0) {
      throw new Error(body.msg || 'API returned non-zero code');
    }

    if (!body.data || !body.data[tokenAddress]) {
      throw new Error('Price data missing for token address');
    }

    const tokenData = body.data[tokenAddress];
    if (!tokenData.quote || !tokenData.quote[currency]) {
      throw new Error(`No quote available in currency ${currency}`);
    }

    const quote = tokenData.quote[currency];
    const priceStr = quote.price;
    const lastUpdated = quote.last_updated;

    const price = parseFloat(priceStr);
    if (!Number.isFinite(price) || price <= 0) {
      throw new Error(`Invalid price value: ${priceStr}`);
    }

    return {
      tokenAddress,
      currency,
      price,
      priceRaw: priceStr,
      lastUpdated,
      lastUpdatedISO:
        typeof lastUpdated === 'number'
          ? new Date(lastUpdated).toISOString()
          : null
    };
  } catch (error) {
    if (error.response) {
      throw new Error(
        `Price API request failed: ${error.response.status} ${error.response.statusText}`
      );
    } else if (error.request) {
      throw new Error('Price API request timeout or network error');
    } else {
      throw error;
    }
  }
}

async function main() {
  try {
    const { tokenInput, currency } = parseArgs();

    console.error(
      `💲 Fetching ${currency} price for ${tokenInput} from Sun Open API...`
    );
    console.error('');

    const { tokenAddress, tokenSymbol } = resolveTokenAddress(tokenInput);

    const result = await getTokenPrice(tokenAddress, currency);

    const output = {
      tokenSymbol: tokenSymbol || tokenInput,
      tokenAddress: result.tokenAddress,
      currency: result.currency,
      price: result.price,
      priceRaw: result.priceRaw,
      lastUpdated: result.lastUpdated,
      lastUpdatedISO: result.lastUpdatedISO
    };

    // JSON to stdout
    console.log(JSON.stringify(output, null, 2));

    // Human-readable summary to stderr
    console.error('✅ Price fetched successfully:');
    console.error(
      `   1 ${output.tokenSymbol} ≈ ${output.price} ${output.currency}`
    );
    if (output.lastUpdatedISO) {
      console.error(`   Last Updated: ${output.lastUpdatedISO}`);
    }
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { getTokenPrice, resolveTokenAddress };

