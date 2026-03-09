#!/usr/bin/env node

/**
 * Unit & integration tests for liquidity.js
 *
 * Run:  node scripts/liquidity.test.js
 *
 * - Pure-function tests always run (no network needed).
 * - On-chain read tests run only when TRON_PRIVATE_KEY is set.
 */

const { computeOptimalAmounts, toRaw, fromRaw, applySlippage } = require('./liquidity');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) {
    passed++;
    console.error(`  ✅ ${msg}`);
  } else {
    failed++;
    console.error(`  ❌ ${msg}`);
  }
}

// ---------------------------------------------------------------------------
// toRaw / fromRaw
// ---------------------------------------------------------------------------
function testConversions() {
  console.error('');
  console.error('🧪 toRaw / fromRaw');

  assert(toRaw('100', 6) === '100000000', 'toRaw("100", 6) === "100000000"');
  assert(toRaw('0.5', 6) === '500000', 'toRaw("0.5", 6) === "500000"');
  assert(toRaw('1.23', 18) === '1230000000000000000', 'toRaw("1.23", 18)');
  assert(toRaw('0', 6) === '0', 'toRaw("0", 6) === "0"');
  assert(toRaw('0.000001', 6) === '1', 'toRaw("0.000001", 6) === "1"');

  assert(fromRaw('100000000', 6) === '100.000000', 'fromRaw("100000000", 6) === "100.000000"');
  assert(fromRaw('500000', 6) === '0.500000', 'fromRaw("500000", 6) === "0.500000"');
  assert(fromRaw('0', 6) === '0.000000', 'fromRaw("0", 6) === "0.000000"');

  // Negative
  assert(fromRaw('-500000', 6) === '-0.500000', 'fromRaw negative');
}

// ---------------------------------------------------------------------------
// applySlippage
// ---------------------------------------------------------------------------
function testSlippage() {
  console.error('');
  console.error('🧪 applySlippage');

  assert(applySlippage('1000000', 5) === '950000', '5% slippage on 1000000');
  assert(applySlippage('1000000', 0) === '1000000', '0% slippage');
  assert(applySlippage('1000000', 10) === '900000', '10% slippage');
}

// ---------------------------------------------------------------------------
// computeOptimalAmounts
// ---------------------------------------------------------------------------
function testOptimal() {
  console.error('');
  console.error('🧪 computeOptimalAmounts');

  // New pool — keep both amounts as-is
  let res = computeOptimalAmounts('100', '200', '0', '0');
  assert(res.amountA === '100' && res.amountB === '200' && !res.adjusted, 'New pool: no adjustment');

  // Balanced pool 1:1 — equal inputs
  res = computeOptimalAmounts('100', '100', '1000', '1000');
  assert(res.amountA === '100' && res.amountB === '100' && !res.adjusted, '1:1 pool, balanced input');

  // Pool ratio 2:1, user supplies 100:100 → should trim B to 50
  res = computeOptimalAmounts('100', '100', '2000', '1000');
  assert(res.amountA === '100' && res.amountB === '50' && res.adjusted, '2:1 pool trims B');

  // Pool ratio 1:2, user supplies 100:100 → should trim A to 50
  res = computeOptimalAmounts('100', '100', '1000', '2000');
  assert(res.amountA === '50' && res.amountB === '100' && res.adjusted, '1:2 pool trims A');

  // Large numbers (simulates real 6-decimal tokens)
  res = computeOptimalAmounts('100000000', '50000000', '1000000000000', '500000000000');
  assert(res.amountA === '100000000' && res.amountB === '50000000' && !res.adjusted, 'Large nums, exact ratio');
}

// ---------------------------------------------------------------------------
// On-chain read (getPairInfo) — only when key is available
// ---------------------------------------------------------------------------
async function testOnChainRead() {
  const pk = process.env.TRON_PRIVATE_KEY || process.env.PRIVATE_KEY;
  if (!pk) {
    console.error('');
    console.error('⏭️  Skipping on-chain tests (no TRON_PRIVATE_KEY set)');
    return;
  }

  const { TronWeb } = require('tronweb');
  const path = require('path');
  const fs = require('fs');
  const { getPairInfo } = require('./liquidity');

  const tokens = JSON.parse(fs.readFileSync(path.join(__dirname, '../resources/common_tokens.json'), 'utf8'));
  const liqContracts = JSON.parse(fs.readFileSync(path.join(__dirname, '../resources/liquidity_manager_contracts.json'), 'utf8'));

  const network = 'nile';
  const tronWeb = new TronWeb({
    fullHost: 'https://nile.trongrid.io',
    privateKey: pk
  });

  const factoryAddress = liqContracts.v2[network].factory.address;
  const wtrxAddress = tokens[network].WTRX.address;
  const usdtAddress = tokens[network].USDT.address;

  console.error('');
  console.error('🧪 On-chain: getPairInfo (WTRX/USDT on nile)');

  try {
    const info = await getPairInfo(tronWeb, factoryAddress, wtrxAddress, usdtAddress);
    assert(typeof info.pairAddress === 'string' || info.pairAddress === null, 'pairAddress is string or null');
    if (info.pairAddress) {
      assert(BigInt(info.reserve0) >= 0n, 'reserve0 >= 0');
      assert(BigInt(info.reserve1) >= 0n, 'reserve1 >= 0');
      assert(BigInt(info.totalSupply) > 0n, 'totalSupply > 0');
      console.error(`     pair=${info.pairAddress}, r0=${info.reserve0}, r1=${info.reserve1}`);
    } else {
      console.error('     Pool does not exist on nile — that is OK for test');
    }
  } catch (e) {
    failed++;
    console.error(`  ❌ getPairInfo threw: ${e.message}`);
  }
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------
async function run() {
  console.error('🧪 Running liquidity.test.js');

  testConversions();
  testSlippage();
  testOptimal();
  await testOnChainRead();

  console.error('');
  console.error(`Results: ${passed} passed, ${failed} failed`);

  const result = { passed, failed, success: failed === 0 };
  console.log(JSON.stringify(result, null, 2));

  if (failed > 0) process.exit(1);
}

if (require.main === module) {
  run();
}
