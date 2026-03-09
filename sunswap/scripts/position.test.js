#!/usr/bin/env node

/**
 * Unit tests for position.js (SunSwap V3)
 *
 * Run:  node scripts/position.test.js
 *
 * - Pure-function tests always run (no network needed).
 * - On-chain read tests run only when TRON_PRIVATE_KEY is set.
 */

const {
  getSqrtRatioAtTick, bigIntSqrt, maxLiquidityForAmounts,
  getAmountsForLiquidity, nearestUsableTick, computeInitialSqrtPriceX96,
  toRaw, fromRaw, applySlippage,
} = require('./position');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.error(`  ✅ ${msg}`); }
  else { failed++; console.error(`  ❌ ${msg}`); }
}

// ---------------------------------------------------------------------------
// bigIntSqrt
// ---------------------------------------------------------------------------
function testBigIntSqrt() {
  console.error('');
  console.error('🧪 bigIntSqrt');

  assert(bigIntSqrt(0n) === 0n, 'sqrt(0) = 0');
  assert(bigIntSqrt(1n) === 1n, 'sqrt(1) = 1');
  assert(bigIntSqrt(4n) === 2n, 'sqrt(4) = 2');
  assert(bigIntSqrt(9n) === 3n, 'sqrt(9) = 3');
  assert(bigIntSqrt(2n) === 1n, 'sqrt(2) = 1 (floor)');
  assert(bigIntSqrt(10n) === 3n, 'sqrt(10) = 3 (floor)');

  const big = 10n ** 36n;
  assert(bigIntSqrt(big) === 10n ** 18n, 'sqrt(10^36) = 10^18');
}

// ---------------------------------------------------------------------------
// getSqrtRatioAtTick
// ---------------------------------------------------------------------------
function testGetSqrtRatioAtTick() {
  console.error('');
  console.error('🧪 getSqrtRatioAtTick');

  // tick 0 → sqrtPriceX96 = 2^96 = 79228162514264337593543950336
  const sqrtAt0 = getSqrtRatioAtTick(0);
  assert(sqrtAt0 === 79228162514264337593543950336n, 'tick 0 → 2^96');

  // tick > 0 → price > 1 → sqrtPrice > 2^96
  const sqrtAtPos = getSqrtRatioAtTick(100);
  assert(sqrtAtPos > sqrtAt0, 'positive tick → larger sqrt');

  // tick < 0 → price < 1 → sqrtPrice < 2^96
  const sqrtAtNeg = getSqrtRatioAtTick(-100);
  assert(sqrtAtNeg < sqrtAt0, 'negative tick → smaller sqrt');

  // Monotonicity: higher tick → higher sqrtPrice
  const sqrt1000 = getSqrtRatioAtTick(1000);
  const sqrt2000 = getSqrtRatioAtTick(2000);
  assert(sqrt2000 > sqrt1000, 'tick 2000 > tick 1000');

  // Symmetry: sqrtRatio(tick) * sqrtRatio(-tick) ≈ (2^96)^2
  const sqrtPos = getSqrtRatioAtTick(5000);
  const sqrtNeg = getSqrtRatioAtTick(-5000);
  const product = sqrtPos * sqrtNeg;
  const q96sq = (1n << 96n) ** 2n;
  const diff = product > q96sq ? product - q96sq : q96sq - product;
  const tolerance = q96sq / 1000n;
  assert(diff < tolerance, 'sqrtRatio(t) * sqrtRatio(-t) ≈ (2^96)^2');

  // Boundary ticks should not throw
  try {
    getSqrtRatioAtTick(-887272);
    getSqrtRatioAtTick(887272);
    assert(true, 'boundary ticks work');
  } catch {
    assert(false, 'boundary ticks work');
  }

  // Out of bounds should throw
  try {
    getSqrtRatioAtTick(887273);
    assert(false, 'out-of-bounds tick should throw');
  } catch {
    assert(true, 'out-of-bounds tick should throw');
  }
}

// ---------------------------------------------------------------------------
// Liquidity math roundtrip
// ---------------------------------------------------------------------------
function testLiquidityMath() {
  console.error('');
  console.error('🧪 Liquidity math');

  const Q96 = 1n << 96n;
  const sqrtPrice = Q96; // tick 0, price = 1
  const sqrtA = getSqrtRatioAtTick(-600);
  const sqrtB = getSqrtRatioAtTick(600);

  const amount0 = 1000000n; // 1 USDT (6 decimals)
  const amount1 = 1000000n; // 1 USDT

  const liq = maxLiquidityForAmounts(sqrtPrice, sqrtA, sqrtB, amount0, amount1);
  assert(liq > 0n, 'computed liquidity > 0');

  const { amount0: got0, amount1: got1 } = getAmountsForLiquidity(sqrtPrice, sqrtA, sqrtB, liq);
  assert(got0 > 0n, 'amount0 > 0');
  assert(got1 > 0n, 'amount1 > 0');

  // Roundtrip: amounts from liquidity should be <= original (due to floor rounding)
  assert(got0 <= amount0, 'roundtrip amount0 <= original');
  assert(got1 <= amount1, 'roundtrip amount1 <= original');

  // Out-of-range: price below range → only token0
  const sqrtBelow = getSqrtRatioAtTick(-1200);
  const liqBelow = maxLiquidityForAmounts(sqrtBelow, sqrtA, sqrtB, amount0, amount1);
  const amtsBelow = getAmountsForLiquidity(sqrtBelow, sqrtA, sqrtB, liqBelow);
  assert(amtsBelow.amount0 > 0n && amtsBelow.amount1 === 0n, 'below range: only token0');

  // Out-of-range: price above range → only token1
  const sqrtAbove = getSqrtRatioAtTick(1200);
  const liqAbove = maxLiquidityForAmounts(sqrtAbove, sqrtA, sqrtB, amount0, amount1);
  const amtsAbove = getAmountsForLiquidity(sqrtAbove, sqrtA, sqrtB, liqAbove);
  assert(amtsAbove.amount0 === 0n && amtsAbove.amount1 > 0n, 'above range: only token1');
}

// ---------------------------------------------------------------------------
// nearestUsableTick
// ---------------------------------------------------------------------------
function testNearestUsableTick() {
  console.error('');
  console.error('🧪 nearestUsableTick');

  assert(nearestUsableTick(0, 60) === 0, 'tick 0, spacing 60 → 0');
  assert(nearestUsableTick(60, 60) === 60, 'tick 60, spacing 60 → 60');
  assert(nearestUsableTick(59, 60) === 60, 'tick 59, spacing 60 → 60');
  assert(nearestUsableTick(30, 60) === 60, 'tick 30, spacing 60 → 60');
  assert(nearestUsableTick(29, 60) === 0, 'tick 29, spacing 60 → 0');
  assert(nearestUsableTick(-30, 60) === 0, 'tick -30, spacing 60 → 0 (JS rounds -0.5 toward +∞)');
  assert(nearestUsableTick(-29, 60) === 0, 'tick -29, spacing 60 → 0');
  assert(nearestUsableTick(100, 10) === 100, 'tick 100, spacing 10 → 100');
  assert(nearestUsableTick(105, 10) === 110, 'tick 105, spacing 10 → 110');
}

// ---------------------------------------------------------------------------
// computeInitialSqrtPriceX96
// ---------------------------------------------------------------------------
function testComputeInitialSqrtPrice() {
  console.error('');
  console.error('🧪 computeInitialSqrtPriceX96');

  const Q96 = 1n << 96n;

  // Equal amounts with equal decimals → price=1 → sqrtPriceX96 ≈ 2^96
  const sqrt1 = computeInitialSqrtPriceX96('1000000', 6, '1000000', 6);
  const diff1 = sqrt1 > Q96 ? sqrt1 - Q96 : Q96 - sqrt1;
  assert(diff1 < Q96 / 1000n, 'equal amounts/decimals → sqrtPriceX96 ≈ 2^96');

  // 4:1 price ratio → sqrtPrice = 2 * 2^96
  const sqrt4 = computeInitialSqrtPriceX96('1000000', 6, '4000000', 6);
  const expected4 = Q96 * 2n;
  const diff4 = sqrt4 > expected4 ? sqrt4 - expected4 : expected4 - sqrt4;
  assert(diff4 < Q96 / 100n, 'price 4 → sqrtPriceX96 ≈ 2 * 2^96');

  // Different decimals: token0 has 18 dec, token1 has 6 dec
  // 1 token0 (1e18) and 1 token1 (1e6) → price = (1e6/1e6) / (1e18/1e18) = 1
  const sqrtDiff = computeInitialSqrtPriceX96('1000000000000000000', 18, '1000000', 6);
  const diffDec = sqrtDiff > Q96 ? sqrtDiff - Q96 : Q96 - sqrtDiff;
  assert(diffDec < Q96 / 1000n, 'different decimals same human amount → ≈ 2^96');
}

// ---------------------------------------------------------------------------
// toRaw / fromRaw / applySlippage (same as liquidity tests)
// ---------------------------------------------------------------------------
function testConversions() {
  console.error('');
  console.error('🧪 toRaw / fromRaw / applySlippage');

  assert(toRaw('100', 6) === '100000000', 'toRaw("100", 6)');
  assert(toRaw('0.5', 6) === '500000', 'toRaw("0.5", 6)');
  assert(toRaw('0', 6) === '0', 'toRaw("0", 6)');
  assert(fromRaw('100000000', 6) === '100.000000', 'fromRaw("100000000", 6)');
  assert(fromRaw('0', 6) === '0.000000', 'fromRaw("0", 6)');
  assert(applySlippage('1000000', 5) === '950000', '5% slippage');
  assert(applySlippage('1000000', 0) === '1000000', '0% slippage');
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------
async function run() {
  console.error('🧪 Running position.test.js (SunSwap V3)');

  testBigIntSqrt();
  testGetSqrtRatioAtTick();
  testLiquidityMath();
  testNearestUsableTick();
  testComputeInitialSqrtPrice();
  testConversions();

  console.error('');
  console.error(`Results: ${passed} passed, ${failed} failed`);

  const result = { passed, failed, success: failed === 0 };
  console.log(JSON.stringify(result, null, 2));

  if (failed > 0) process.exit(1);
}

if (require.main === module) { run(); }
