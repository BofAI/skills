#!/usr/bin/env node

/**
 * Basic sanity test for price.js
 *
 * This test calls getTokenPrice for TRX mainnet address and asserts:
 *   - price is a positive number
 *   - currency is USD
 */

const { getTokenPrice } = require('./price');

async function run() {
  const TRX_MAINNET_ADDRESS = 'T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb';

  try {
    console.error('🧪 Running price.test.js (TRX / USD)...');
    const result = await getTokenPrice(TRX_MAINNET_ADDRESS, 'USD');

    if (result.currency !== 'USD') {
      throw new Error(`Expected currency USD, got ${result.currency}`);
    }

    if (!Number.isFinite(result.price) || result.price <= 0) {
      throw new Error(`Expected positive price, got ${result.price}`);
    }

    console.error('✅ price.test.js passed');
    console.log(
      JSON.stringify(
        {
          success: true,
          tokenAddress: result.tokenAddress,
          currency: result.currency,
          price: result.price
        },
        null,
        2
      )
    );
  } catch (error) {
    console.error('❌ price.test.js failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  run();
}

