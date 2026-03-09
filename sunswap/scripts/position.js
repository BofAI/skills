#!/usr/bin/env node

/**
 * SunSwap V3 Position Management Script
 *
 * Commands:
 *   node position.js positions [--network nile|mainnet]
 *   node position.js add TOKEN_A TOKEN_B AMT_A AMT_B --fee N --tick-lower N --tick-upper N [OPTIONS]
 *   node position.js remove [TOKEN_A TOKEN_B --fee N --tick-lower N --tick-upper N | --position-id N] [--percent N] [OPTIONS]
 *   node position.js collect [TOKEN_A TOKEN_B --fee N --tick-lower N --tick-upper N | --position-id N] [OPTIONS]
 *
 * Options:
 *   --network <nile|mainnet>     Network (default: nile)
 *   --slippage <5>               Slippage tolerance % (default: 5)
 *   --execute                    Execute on-chain (without this, dry-run only)
 *   --check-only                 Read-only check
 *   --approve-only               Only approve tokens (requires --execute)
 *   --create-pool                Create pool if it doesn't exist (add only)
 *   --position-id <N>            Position NFT token ID
 *   --percent <0-100>            Percentage to remove (default: 100)
 *
 * Fee tiers (--fee):  100 (0.01%), 500 (0.05%), 3000 (0.3%), 10000 (1%)
 *
 * Workflow (each private-key step needs explicit --execute):
 *   1. node position.js add TRX USDT 100 15 --fee 3000 --tick-lower -60 --tick-upper 60 --check-only
 *   2. node position.js add TRX USDT 100 15 --fee 3000 --tick-lower -60 --tick-upper 60 --approve-only --execute
 *   3. node position.js add TRX USDT 100 15 --fee 3000 --tick-lower -60 --tick-upper 60 --execute
 */

const { TronWeb } = require('tronweb');

const path = require('path');
const fs = require('fs');
const { getPrivateKeyOrExit, sleep } = require('./utils');

// ---------------------------------------------------------------------------
// Resources
// ---------------------------------------------------------------------------
const tokensPath = path.join(__dirname, '../resources/common_tokens.json');
const contractsPath = path.join(__dirname, '../resources/liquidity_manager_contracts.json');
const allTokens = JSON.parse(fs.readFileSync(tokensPath, 'utf8'));
const allContracts = JSON.parse(fs.readFileSync(contractsPath, 'utf8'));

const TRX_ADDRESS = 'T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb';
const TRON_ENDPOINTS = {
  mainnet: { fullHost: 'https://api.trongrid.io', apiKey: process.env.TRONGRID_API_KEY || '' },
  nile: { fullHost: 'https://nile.trongrid.io', apiKey: '' }
};

const MAX_UINT256 = '115792089237316195423570985008687907853269984665640564039457584007913129639935';
const MAX_UINT128 = '340282366920938463463374607431768211455';
const FEE_TICK_SPACING = { 100: 1, 500: 10, 3000: 60, 10000: 200 };
const FEE_LABELS = { 100: '0.01%', 500: '0.05%', 3000: '0.3%', 10000: '1%' };


// ---------------------------------------------------------------------------
// ABIs
// ---------------------------------------------------------------------------
const v3Abi = allContracts.v3.abi;

const PM_ABI = [
  v3Abi.mint, v3Abi.increaseLiquidity, v3Abi.decreaseLiquidity,
  v3Abi.collect, v3Abi.burn, v3Abi.positions,
  v3Abi.createAndInitializePoolIfNecessary,
  v3Abi.balanceOf, v3Abi.tokenOfOwnerByIndex,
];

const PM_VIEW_ABI = [
  v3Abi.collectView, v3Abi.positions,
  v3Abi.balanceOf, v3Abi.tokenOfOwnerByIndex,
];

const FACTORY_ABI = [v3Abi.getPool];
const POOL_ABI = [v3Abi.slot0, v3Abi.poolLiquidity, v3Abi.poolTickSpacing];
const TRC20_ABI = [v3Abi.allowance, v3Abi.approve, v3Abi.balanceOf];

// ---------------------------------------------------------------------------
// V3 Math — ported from Uniswap V3 TickMath.sol & LiquidityAmounts.sol
// ---------------------------------------------------------------------------
const Q96 = 1n << 96n;
const MIN_TICK = -887272;
const MAX_TICK_VAL = 887272;

function getSqrtRatioAtTick(tick) {
  const absTick = tick < 0 ? -tick : tick;
  if (absTick > MAX_TICK_VAL) throw new Error(`Tick ${tick} out of bounds [${MIN_TICK}, ${MAX_TICK_VAL}]`);

  let ratio = (absTick & 0x1) !== 0
    ? 0xfffcb933bd6fad37aa2d162d1a594001n
    : 0x100000000000000000000000000000000n;

  if ((absTick & 0x2) !== 0) ratio = (ratio * 0xfff97272373d413259a46990580e213an) >> 128n;
  if ((absTick & 0x4) !== 0) ratio = (ratio * 0xfff2e50f5f656932ef12357cf3c7fdccn) >> 128n;
  if ((absTick & 0x8) !== 0) ratio = (ratio * 0xffe5caca7e10e4e61c3624eaa0941cd0n) >> 128n;
  if ((absTick & 0x10) !== 0) ratio = (ratio * 0xffcb9843d60f6159c9db58835c926644n) >> 128n;
  if ((absTick & 0x20) !== 0) ratio = (ratio * 0xff973b41fa98c081472e6896dfb254c0n) >> 128n;
  if ((absTick & 0x40) !== 0) ratio = (ratio * 0xff2ea16466c96a3843ec78b326b52861n) >> 128n;
  if ((absTick & 0x80) !== 0) ratio = (ratio * 0xfe5dee046a99a2a811c461f1969c3053n) >> 128n;
  if ((absTick & 0x100) !== 0) ratio = (ratio * 0xfcbe86c7900a88aedcffc83b479aa3a4n) >> 128n;
  if ((absTick & 0x200) !== 0) ratio = (ratio * 0xf987a7253ac413176f2b074cf7815e54n) >> 128n;
  if ((absTick & 0x400) !== 0) ratio = (ratio * 0xf3392b0822b70005940c7a398e4b70f3n) >> 128n;
  if ((absTick & 0x800) !== 0) ratio = (ratio * 0xe7159475a2c29b7443b29c7fa6e889d9n) >> 128n;
  if ((absTick & 0x1000) !== 0) ratio = (ratio * 0xd097f3bdfd2022b8845ad8f792aa5825n) >> 128n;
  if ((absTick & 0x2000) !== 0) ratio = (ratio * 0xa9f746462d870fdf8a65dc1f90e061e5n) >> 128n;
  if ((absTick & 0x4000) !== 0) ratio = (ratio * 0x70d869a156d2a1b890bb3df62baf32f7n) >> 128n;
  if ((absTick & 0x8000) !== 0) ratio = (ratio * 0x31be135f97d08fd981231505542fcfa6n) >> 128n;
  if ((absTick & 0x10000) !== 0) ratio = (ratio * 0x9aa508b5b7a84e1c677de54f3e99bc9n) >> 128n;
  if ((absTick & 0x20000) !== 0) ratio = (ratio * 0x5d6af8dedb81196699c329225ee604n) >> 128n;
  if ((absTick & 0x40000) !== 0) ratio = (ratio * 0x2216e584f5fa1ea926041bedfe98n) >> 128n;
  if ((absTick & 0x80000) !== 0) ratio = (ratio * 0x48a170391f7dc42444e8fa2n) >> 128n;

  if (tick > 0) ratio = ((1n << 256n) - 1n) / ratio;
  return (ratio >> 32n) + ((ratio % (1n << 32n)) > 0n ? 1n : 0n);
}

function bigIntSqrt(n) {
  if (n < 0n) throw new Error('Negative sqrt input');
  if (n === 0n) return 0n;
  let x = n;
  let y = (x + 1n) / 2n;
  while (y < x) { x = y; y = (x + n / x) / 2n; }
  return x;
}

function getLiquidityForAmount0(sqrtA, sqrtB, amount0) {
  if (sqrtA > sqrtB) [sqrtA, sqrtB] = [sqrtB, sqrtA];
  return (BigInt(amount0) * sqrtA * sqrtB / Q96) / (sqrtB - sqrtA);
}

function getLiquidityForAmount1(sqrtA, sqrtB, amount1) {
  if (sqrtA > sqrtB) [sqrtA, sqrtB] = [sqrtB, sqrtA];
  return (BigInt(amount1) * Q96) / (sqrtB - sqrtA);
}

function maxLiquidityForAmounts(sqrtPrice, sqrtA, sqrtB, amount0, amount1) {
  if (sqrtA > sqrtB) [sqrtA, sqrtB] = [sqrtB, sqrtA];
  if (sqrtPrice <= sqrtA) return getLiquidityForAmount0(sqrtA, sqrtB, amount0);
  if (sqrtPrice < sqrtB) {
    const liq0 = getLiquidityForAmount0(sqrtPrice, sqrtB, amount0);
    const liq1 = getLiquidityForAmount1(sqrtA, sqrtPrice, amount1);
    return liq0 < liq1 ? liq0 : liq1;
  }
  return getLiquidityForAmount1(sqrtA, sqrtB, amount1);
}

function getAmount0ForLiquidity(sqrtA, sqrtB, liquidity) {
  if (sqrtA > sqrtB) [sqrtA, sqrtB] = [sqrtB, sqrtA];
  return (BigInt(liquidity) * Q96 * (sqrtB - sqrtA)) / (sqrtB * sqrtA);
}

function getAmount1ForLiquidity(sqrtA, sqrtB, liquidity) {
  if (sqrtA > sqrtB) [sqrtA, sqrtB] = [sqrtB, sqrtA];
  return (BigInt(liquidity) * (sqrtB - sqrtA)) / Q96;
}

function getAmountsForLiquidity(sqrtPrice, sqrtA, sqrtB, liquidity) {
  if (sqrtA > sqrtB) [sqrtA, sqrtB] = [sqrtB, sqrtA];
  let amount0 = 0n, amount1 = 0n;
  if (sqrtPrice <= sqrtA) {
    amount0 = getAmount0ForLiquidity(sqrtA, sqrtB, liquidity);
  } else if (sqrtPrice < sqrtB) {
    amount0 = getAmount0ForLiquidity(sqrtPrice, sqrtB, liquidity);
    amount1 = getAmount1ForLiquidity(sqrtA, sqrtPrice, liquidity);
  } else {
    amount1 = getAmount1ForLiquidity(sqrtA, sqrtB, liquidity);
  }
  return { amount0, amount1 };
}

function nearestUsableTick(tick, tickSpacing) {
  const rounded = Math.round(tick / tickSpacing) * tickSpacing;
  return Math.max(MIN_TICK, Math.min(MAX_TICK_VAL, rounded));
}

function computeInitialSqrtPriceX96(amount0Raw, decimals0, amount1Raw, decimals1) {
  const Q192 = 1n << 192n;
  const num = BigInt(amount1Raw) * (10n ** BigInt(decimals0)) * Q192;
  const den = BigInt(amount0Raw) * (10n ** BigInt(decimals1));
  if (den === 0n) throw new Error('Cannot compute price with zero amount0');
  return bigIntSqrt(num / den);
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function toRaw(amount, decimals) {
  const parts = amount.toString().split('.');
  const whole = parts[0] || '0';
  let frac = parts[1] || '';
  if (frac.length > decimals) frac = frac.substring(0, decimals);
  else frac = frac.padEnd(decimals, '0');
  return BigInt(whole + frac).toString();
}

function fromRaw(rawStr, decimals) {
  let negative = false;
  let raw = BigInt(rawStr);
  if (raw < 0n) { negative = true; raw = -raw; }
  const divisor = 10n ** BigInt(decimals);
  const whole = raw / divisor;
  const frac = (raw % divisor).toString().padStart(decimals, '0');
  return `${negative ? '-' : ''}${whole}.${frac}`;
}

function applySlippage(amountStr, slippagePct) {
  const amount = BigInt(amountStr);
  const factor = BigInt(Math.floor((1 - slippagePct / 100) * 10000));
  return (amount * factor / 10000n).toString();
}

function isTRX(tokenInfo) {
  return tokenInfo.address === TRX_ADDRESS || tokenInfo.symbol === 'TRX';
}

function getTokenInfo(symbolOrAddress, network) {
  const networkTokens = allTokens[network];
  if (!networkTokens) throw new Error(`Unknown network: ${network}`);
  if (symbolOrAddress.startsWith('T') && symbolOrAddress.length === 34) {
    for (const [key, token] of Object.entries(networkTokens)) {
      if (token.address === symbolOrAddress) return { ...token, symbol: key };
    }
    return { symbol: 'UNKNOWN', address: symbolOrAddress, decimals: 6 };
  }
  const token = networkTokens[symbolOrAddress];
  if (!token) throw new Error(`Unknown token: ${symbolOrAddress} on ${network}`);
  return { ...token, symbol: symbolOrAddress };
}

function getTokenInfoByAddress(address, network) {
  const networkTokens = allTokens[network];
  for (const [sym, info] of Object.entries(networkTokens)) {
    if (info.address === address) return { ...info, symbol: sym };
  }
  return { symbol: address.slice(0, 8) + '...', address, decimals: 6 };
}

function getWTRXAddress(network) {
  const wtrx = allTokens[network].WTRX;
  if (!wtrx) throw new Error(`WTRX not configured for network: ${network}`);
  return wtrx.address;
}

function pairAddr(tokenInfo, network) {
  return isTRX(tokenInfo) ? getWTRXAddress(network) : tokenInfo.address;
}

function displaySym(info) {
  return isTRX(info) ? `${info.symbol}(WTRX)` : info.symbol;
}

function sortTokens(tronWeb, tokenAInfo, tokenBInfo, network) {
  const addrA = pairAddr(tokenAInfo, network);
  const addrB = pairAddr(tokenBInfo, network);
  const hexA = tronWeb.address.toHex(addrA).toLowerCase();
  const hexB = tronWeb.address.toHex(addrB).toLowerCase();
  if (hexA === hexB) throw new Error('Identical token addresses');
  if (hexA < hexB) return { token0Info: tokenAInfo, token1Info: tokenBInfo, swapped: false };
  return { token0Info: tokenBInfo, token1Info: tokenAInfo, swapped: true };
}

// ---------------------------------------------------------------------------
// On-chain reads
// ---------------------------------------------------------------------------
async function getBalance(tronWeb, tokenAddress, wallet) {
  if (tokenAddress === TRX_ADDRESS) return (await tronWeb.trx.getBalance(wallet)).toString();
  const c = await tronWeb.contract(TRC20_ABI, tokenAddress);
  return (await c.balanceOf(wallet).call()).toString();
}

async function getAllowance(tronWeb, tokenAddress, owner, spender) {
  if (tokenAddress === TRX_ADDRESS) return MAX_UINT256;
  const c = await tronWeb.contract(TRC20_ABI, tokenAddress);
  return (await c.allowance(owner, spender).call()).toString();
}

async function approveToken(tronWeb, tokenAddress, spender) {
  console.error(`   📝 Approving ${tokenAddress} for position manager...`);
  const c = await tronWeb.contract(TRC20_ABI, tokenAddress);
  const tx = await c.approve(spender, MAX_UINT256).send({ feeLimit: 100_000_000 });
  console.error(`   ✅ Approval tx: ${tx}`);
  console.error('   ⏳ Waiting 15 s for confirmation...');
  await sleep(15000);
  return tx;
}

async function getPoolInfo(tronWeb, factoryAddr, token0Addr, token1Addr, fee) {
  const factory = await tronWeb.contract(FACTORY_ABI, factoryAddr);
  const poolHex = await factory.getPool(token0Addr, token1Addr, fee).call();
  const poolBase58 = tronWeb.address.fromHex(poolHex);
  const ZERO = tronWeb.address.fromHex('410000000000000000000000000000000000000000');
  if (!poolBase58 || poolBase58 === ZERO) return null;

  const pool = await tronWeb.contract(POOL_ABI, poolBase58);
  const s0 = await pool.slot0().call();
  const liq = await pool.liquidity().call();
  const ts = await pool.tickSpacing().call();

  return {
    poolAddress: poolBase58,
    sqrtPriceX96: (s0.sqrtPriceX96 || s0[0]).toString(),
    tick: Number(s0.tick ?? s0[1]),
    liquidity: liq.toString(),
    tickSpacing: Number(ts),
  };
}

async function getPositionOnChain(tronWeb, pmAddr, tokenId) {
  const pm = await tronWeb.contract(PM_ABI, pmAddr);
  const p = await pm.positions(tokenId).call();
  return {
    token0: tronWeb.address.fromHex(p.token0 || p[2]),
    token1: tronWeb.address.fromHex(p.token1 || p[3]),
    fee: Number(p.fee ?? p[4]),
    tickLower: Number(p.tickLower ?? p[5]),
    tickUpper: Number(p.tickUpper ?? p[6]),
    liquidity: (p.liquidity || p[7]).toString(),
  };
}

async function findPositionByParams(tronWeb, pmAddr, wallet, token0Addr, token1Addr, fee, tickLower, tickUpper) {
  const pm = await tronWeb.contract(PM_ABI, pmAddr);
  const count = Number(await pm.balanceOf(wallet).call());
  for (let i = 0; i < count; i++) {
    const tokenId = (await pm.tokenOfOwnerByIndex(wallet, i).call()).toString();
    const pos = await getPositionOnChain(tronWeb, pmAddr, tokenId);
    if (pos.token0 === token0Addr && pos.token1 === token1Addr &&
      pos.fee === fee && pos.tickLower === tickLower && pos.tickUpper === tickUpper) {
      return { tokenId, ...pos };
    }
  }
  return null;
}

async function estimateFees(tronWeb, pmAddr, tokenId, wallet) {
  const pm = await tronWeb.contract(PM_VIEW_ABI, pmAddr);
  const result = await pm.collect([tokenId, wallet, MAX_UINT128, MAX_UINT128]).call({ from: wallet });
  return {
    fee0: (result.amount0 || result[0]).toString(),
    fee1: (result.amount1 || result[1]).toString(),
  };
}

// ---------------------------------------------------------------------------
// Handler: positions (list user's V3 positions)
// ---------------------------------------------------------------------------
async function handlePositions(tronWeb, opts) {
  const { network, walletAddress } = opts;
  console.error('📋 Fetching V3 positions on-chain...');

  const pmAddr = allContracts.v3[network].positionManager.address;
  const pm = await tronWeb.contract(PM_ABI, pmAddr);
  const count = Number(await pm.balanceOf(walletAddress).call());
  console.error(`   Found ${count} NFT position(s)`);

  const positions = [];
  for (let i = 0; i < count; i++) {
    const tokenId = (await pm.tokenOfOwnerByIndex(walletAddress, i).call()).toString();
    const pos = await getPositionOnChain(tronWeb, pmAddr, tokenId);
    const t0 = getTokenInfoByAddress(pos.token0, network);
    const t1 = getTokenInfoByAddress(pos.token1, network);
    positions.push({ tokenId, ...pos, token0Symbol: t0.symbol, token1Symbol: t1.symbol });
    console.error(`   #${tokenId}: ${t0.symbol}/${t1.symbol} fee=${pos.fee} tick=[${pos.tickLower},${pos.tickUpper}] liq=${pos.liquidity}`);
  }
  console.log(JSON.stringify({ positions, count, source: 'onchain' }, null, 2));
}

// ---------------------------------------------------------------------------
// Handler: add (mint or increaseLiquidity)
// ---------------------------------------------------------------------------
async function handleAdd(tronWeb, opts) {
  const {
    token0Info, token1Info, amount0Raw, amount1Raw,
    fee, tickLower, tickUpper,
    network, slippage, execute, checkOnly, approveOnly, createPool,
    positionId, walletAddress
  } = opts;

  const v3Cfg = allContracts.v3[network];
  const pmAddr = v3Cfg.positionManager.address;
  const factoryAddr = v3Cfg.factory.address;
  const token0Addr = pairAddr(token0Info, network);
  const token1Addr = pairAddr(token1Info, network);

  if (isTRX(token0Info) || isTRX(token1Info))
    console.error('   ℹ️  TRX auto-substituted to WTRX for V3 (need WTRX balance)\n');

  // ---- Step 1: Pool --------------------------------------------------------
  console.error('📊 Step 1: Checking pool...');
  let poolInfo = await getPoolInfo(tronWeb, factoryAddr, token0Addr, token1Addr, fee);

  if (!poolInfo) {
    console.error('   ⚠️  Pool does not exist!');
    if (!createPool) {
      const r = { action: 'addPosition', status: 'pool_not_found', poolExists: false, hint: 'Use --create-pool --execute to create' };
      console.log(JSON.stringify(r, null, 2)); return;
    }
    if (checkOnly) {
      const sqrtInit = computeInitialSqrtPriceX96(amount0Raw, token0Info.decimals, amount1Raw, token1Info.decimals);
      const r = { action: 'addPosition', status: 'pool_not_found', willCreatePool: true, initialSqrtPriceX96: sqrtInit.toString() };
      console.log(JSON.stringify(r, null, 2)); return;
    }
    if (!execute) {
      console.error('   DRY RUN: would create pool (use --execute)');
      console.log(JSON.stringify({ dryRun: true, action: 'createPool', token0: token0Info.symbol, token1: token1Info.symbol, fee })); return;
    }
    console.error('   Creating pool...');
    const sqrtInit = computeInitialSqrtPriceX96(amount0Raw, token0Info.decimals, amount1Raw, token1Info.decimals);
    const pm = await tronWeb.contract(PM_ABI, pmAddr);
    const txC = await pm.createAndInitializePoolIfNecessary(token0Addr, token1Addr, fee, sqrtInit.toString()).send({ feeLimit: 1_000_000_000 });
    console.error(`   ✅ Pool created: ${txC}`);
    await sleep(5000);
    poolInfo = await getPoolInfo(tronWeb, factoryAddr, token0Addr, token1Addr, fee);
    if (!poolInfo) throw new Error('Pool creation failed');
  }

  console.error(`   Pool: ${poolInfo.poolAddress}`);
  console.error(`   Current tick: ${poolInfo.tick},  sqrtPriceX96: ${poolInfo.sqrtPriceX96}`);

  // ---- Step 2: Existing position -------------------------------------------
  console.error('');
  console.error('🔍 Step 2: Checking existing position...');
  let existing = null;
  if (positionId) {
    existing = await getPositionOnChain(tronWeb, pmAddr, positionId);
    existing.tokenId = positionId;
    console.error(`   Found position #${positionId} (provided)`);
  } else {
    existing = await findPositionByParams(tronWeb, pmAddr, walletAddress, token0Addr, token1Addr, fee, tickLower, tickUpper);
    if (existing) console.error(`   Found existing position #${existing.tokenId}`);
    else console.error('   No existing position — will mint new');
  }
  const isIncrease = !!existing;
  const action = isIncrease ? 'increaseLiquidity' : 'mint';

  // ---- Step 3: Estimate amounts --------------------------------------------
  console.error('');
  console.error('🔢 Step 3: Estimating amounts...');
  const sqrtPriceX96 = BigInt(poolInfo.sqrtPriceX96);
  const sqrtA = getSqrtRatioAtTick(tickLower);
  const sqrtB = getSqrtRatioAtTick(tickUpper);
  const liquidity = maxLiquidityForAmounts(sqrtPriceX96, sqrtA, sqrtB, BigInt(amount0Raw), BigInt(amount1Raw));
  const { amount0: est0, amount1: est1 } = getAmountsForLiquidity(sqrtPriceX96, sqrtA, sqrtB, liquidity);

  console.error(`   Estimated liquidity: ${liquidity}`);
  console.error(`   ${displaySym(token0Info)}: ${fromRaw(amount0Raw, token0Info.decimals)} → ~${fromRaw(est0.toString(), token0Info.decimals)}`);
  console.error(`   ${displaySym(token1Info)}: ${fromRaw(amount1Raw, token1Info.decimals)} → ~${fromRaw(est1.toString(), token1Info.decimals)}`);

  // ---- Step 4: Balances ----------------------------------------------------
  console.error('');
  console.error('💰 Step 4: Checking balances...');
  const bal0 = await getBalance(tronWeb, token0Addr, walletAddress);
  const bal1 = await getBalance(tronWeb, token1Addr, walletAddress);
  console.error(`   ${displaySym(token0Info)}: ${fromRaw(bal0, token0Info.decimals)} (need ${fromRaw(amount0Raw, token0Info.decimals)})`);
  console.error(`   ${displaySym(token1Info)}: ${fromRaw(bal1, token1Info.decimals)} (need ${fromRaw(amount1Raw, token1Info.decimals)})`);
  if (BigInt(bal0) < BigInt(amount0Raw)) throw new Error(`Insufficient ${displaySym(token0Info)} balance`);
  if (BigInt(bal1) < BigInt(amount1Raw)) throw new Error(`Insufficient ${displaySym(token1Info)} balance`);

  // ---- Step 5: Approvals (V3 always uses TRC20, including WTRX) -----------
  console.error('');
  console.error('🔐 Step 5: Checking approvals...');
  const pendingApprovals = [];
  for (const [info, addr, amt] of [[token0Info, token0Addr, amount0Raw], [token1Info, token1Addr, amount1Raw]]) {
    const allowance = await getAllowance(tronWeb, addr, walletAddress, pmAddr);
    if (BigInt(allowance) < BigInt(amt)) {
      console.error(`   ${displaySym(info)}: allowance insufficient ❌`);
      pendingApprovals.push({ info, addr });
    } else {
      console.error(`   ${displaySym(info)}: allowance OK ✅`);
    }
  }

  // ---- check-only ----------------------------------------------------------
  if (checkOnly) {
    console.error('');
    console.error('✅ Check complete (--check-only)');
    const result = {
      action, poolExists: true, pool: poolInfo.poolAddress, currentTick: poolInfo.tick,
      tickLower, tickUpper, fee: `${fee} (${FEE_LABELS[fee]})`,
      existingPositionId: existing?.tokenId || null,
      estimatedLiquidity: liquidity.toString(),
      token0: { symbol: token0Info.symbol, desired: fromRaw(amount0Raw, token0Info.decimals), estimated: fromRaw(est0.toString(), token0Info.decimals) },
      token1: { symbol: token1Info.symbol, desired: fromRaw(amount1Raw, token1Info.decimals), estimated: fromRaw(est1.toString(), token1Info.decimals) },
      needsApproval: pendingApprovals.map(t => t.info.symbol),
      readyToExecute: pendingApprovals.length === 0,
    };
    console.log(JSON.stringify(result, null, 2)); return;
  }

  // ---- approve-only --------------------------------------------------------
  if (approveOnly) {
    if (pendingApprovals.length === 0) {
      console.error('\n✅ All tokens already approved');
      console.log(JSON.stringify({ approved: [], message: 'All tokens already have sufficient allowance' })); return;
    }
    if (!execute) {
      console.error('   DRY RUN: would approve ' + pendingApprovals.map(t => displaySym(t.info)).join(', '));
      console.log(JSON.stringify({ dryRun: true, action: 'approve', tokens: pendingApprovals.map(t => t.info.symbol) })); return;
    }
    const txs = [];
    for (const t of pendingApprovals) {
      const tx = await approveToken(tronWeb, t.addr, pmAddr);
      txs.push({ symbol: t.info.symbol, transaction: tx });
    }
    console.error('\n✅ Approval complete. Run --execute to add position.');
    console.log(JSON.stringify({ approved: txs }, null, 2)); return;
  }

  // ---- execute (refuse if approvals pending) -------------------------------
  if (pendingApprovals.length > 0) {
    console.error('\n🚨 Approval required!');
    console.error(`   Tokens: ${pendingApprovals.map(t => displaySym(t.info)).join(', ')}`);
    console.error('   Run --approve-only --execute first');
    console.log(JSON.stringify({ action, status: 'approval_required', needsApproval: pendingApprovals.map(t => t.info.symbol) }, null, 2));
    return;
  }

  if (!execute) {
    console.error('   DRY RUN (use --execute)');
    console.log(JSON.stringify({ dryRun: true, action, pool: poolInfo.poolAddress, tickLower, tickUpper, fee }));
    return;
  }

  // ---- Step 6: Execute -----------------------------------------------------
  console.error('');
  console.error(`💱 Step 6: ${action}...`);
  const deadline = Math.floor(Date.now() / 1000) + 300;
  const amount0Min = applySlippage(est0.toString(), slippage);
  const amount1Min = applySlippage(est1.toString(), slippage);

  const pm = await tronWeb.contract(PM_ABI, pmAddr);
  let tx;
  if (isIncrease) {
    console.error(`   increaseLiquidity(#${existing.tokenId})...`);
    tx = await pm.increaseLiquidity([existing.tokenId, amount0Raw, amount1Raw, amount0Min, amount1Min, deadline]).send({ feeLimit: 1_000_000_000 });
  } else {
    console.error('   mint()...');
    tx = await pm.mint([token0Addr, token1Addr, fee, tickLower, tickUpper, amount0Raw, amount1Raw, amount0Min, amount1Min, walletAddress, deadline]).send({ feeLimit: 1_000_000_000 });
  }
  console.error(`   ✅ Tx: ${tx}`);

  // Post-check
  console.error('\n📊 Checking results...');
  await sleep(5000);
  let resultPosId = existing?.tokenId;
  if (!isIncrease) {
    const newPos = await findPositionByParams(tronWeb, pmAddr, walletAddress, token0Addr, token1Addr, fee, tickLower, tickUpper);
    resultPosId = newPos?.tokenId;
  }
  if (resultPosId) {
    const up = await getPositionOnChain(tronWeb, pmAddr, resultPosId);
    console.error(`   Position #${resultPosId}: liquidity=${up.liquidity}`);
  }

  const explorerBase = network === 'mainnet' ? 'https://tronscan.org' : 'https://nile.tronscan.org';
  console.log(JSON.stringify({
    success: true, action, transaction: tx,
    explorer: `${explorerBase}/#/transaction/${tx}`,
    positionId: resultPosId, pool: poolInfo.poolAddress, tickLower, tickUpper, fee,
    token0: { symbol: token0Info.symbol, amount: fromRaw(amount0Raw, token0Info.decimals) },
    token1: { symbol: token1Info.symbol, amount: fromRaw(amount1Raw, token1Info.decimals) },
  }, null, 2));
}

// ---------------------------------------------------------------------------
// Handler: remove (decreaseLiquidity + collect)
// ---------------------------------------------------------------------------
async function handleRemove(tronWeb, opts) {
  const {
    network, slippage, execute, checkOnly,
    positionId, percent, walletAddress,
    token0Info, token1Info, fee, tickLower, tickUpper
  } = opts;

  const v3Cfg = allContracts.v3[network];
  const pmAddr = v3Cfg.positionManager.address;
  const factoryAddr = v3Cfg.factory.address;

  // ---- Step 1: Find position -----------------------------------------------
  console.error('📊 Step 1: Finding position...');
  let position, tokenId;
  if (positionId) {
    position = await getPositionOnChain(tronWeb, pmAddr, positionId);
    tokenId = positionId;
  } else {
    const t0Addr = pairAddr(token0Info, network);
    const t1Addr = pairAddr(token1Info, network);
    const found = await findPositionByParams(tronWeb, pmAddr, walletAddress, t0Addr, t1Addr, fee, tickLower, tickUpper);
    if (!found) throw new Error('Position not found');
    position = found; tokenId = found.tokenId;
  }
  console.error(`   Position #${tokenId}`);
  console.error(`   Liquidity: ${position.liquidity}`);
  if (BigInt(position.liquidity) === 0n) throw new Error('Position has no liquidity');

  // ---- Step 2: Compute removal ---------------------------------------------
  console.error('');
  console.error('🔢 Step 2: Computing removal...');
  const liquidityToRemove = BigInt(position.liquidity) * BigInt(percent) / 100n;
  console.error(`   Removing ${percent}%: ${liquidityToRemove} liquidity`);

  const poolInfo = await getPoolInfo(tronWeb, factoryAddr, position.token0, position.token1, position.fee);
  if (!poolInfo) throw new Error('Pool not found');

  const sqrtPrice = BigInt(poolInfo.sqrtPriceX96);
  const sqrtA = getSqrtRatioAtTick(position.tickLower);
  const sqrtB = getSqrtRatioAtTick(position.tickUpper);
  const { amount0, amount1 } = getAmountsForLiquidity(sqrtPrice, sqrtA, sqrtB, liquidityToRemove);

  const t0 = getTokenInfoByAddress(position.token0, network);
  const t1 = getTokenInfoByAddress(position.token1, network);
  console.error(`   Expected ${t0.symbol}: ~${fromRaw(amount0.toString(), t0.decimals)}`);
  console.error(`   Expected ${t1.symbol}: ~${fromRaw(amount1.toString(), t1.decimals)}`);

  const remainingLiq = BigInt(position.liquidity) - liquidityToRemove;
  const rem = getAmountsForLiquidity(sqrtPrice, sqrtA, sqrtB, remainingLiq);
  console.error(`   Remaining liquidity: ${remainingLiq}`);

  // ---- check-only ----------------------------------------------------------
  if (checkOnly) {
    console.error('\n✅ Check complete (--check-only)');
    console.log(JSON.stringify({
      action: 'decreaseLiquidity', positionId: tokenId, percent,
      liquidityToRemove: liquidityToRemove.toString(),
      expectedToken0: { symbol: t0.symbol, amount: fromRaw(amount0.toString(), t0.decimals) },
      expectedToken1: { symbol: t1.symbol, amount: fromRaw(amount1.toString(), t1.decimals) },
      remainingLiquidity: remainingLiq.toString(),
      remainingToken0: { symbol: t0.symbol, amount: fromRaw(rem.amount0.toString(), t0.decimals) },
      remainingToken1: { symbol: t1.symbol, amount: fromRaw(rem.amount1.toString(), t1.decimals) },
      readyToExecute: true,
    }, null, 2)); return;
  }

  if (!execute) {
    console.log(JSON.stringify({ dryRun: true, action: 'decreaseLiquidity', positionId: tokenId, percent })); return;
  }

  // ---- Step 3: decreaseLiquidity -------------------------------------------
  console.error('\n💱 Step 3: Decreasing liquidity...');
  const deadline = Math.floor(Date.now() / 1000) + 300;
  const amount0Min = applySlippage(amount0.toString(), slippage);
  const amount1Min = applySlippage(amount1.toString(), slippage);

  const pm = await tronWeb.contract(PM_ABI, pmAddr);
  const tx1 = await pm.decreaseLiquidity([tokenId, liquidityToRemove.toString(), amount0Min, amount1Min, deadline]).send({ feeLimit: 1_000_000_000 });
  console.error(`   ✅ decreaseLiquidity tx: ${tx1}`);
  await sleep(5000);

  // ---- Step 4: collect -----------------------------------------------------
  console.error('\n💰 Step 4: Collecting tokens...');
  const tx2 = await pm.collect([tokenId, walletAddress, MAX_UINT128, MAX_UINT128]).send({ feeLimit: 1_000_000_000 });
  console.error(`   ✅ collect tx: ${tx2}`);

  await sleep(5000);
  const updated = await getPositionOnChain(tronWeb, pmAddr, tokenId);
  console.error(`   Remaining liquidity: ${updated.liquidity}`);

  const explorerBase = network === 'mainnet' ? 'https://tronscan.org' : 'https://nile.tronscan.org';
  console.log(JSON.stringify({
    success: true, action: 'decreaseLiquidity', positionId: tokenId, percent,
    transactions: { decreaseLiquidity: tx1, collect: tx2 },
    explorer: `${explorerBase}/#/transaction/${tx1}`,
    expectedToken0: { symbol: t0.symbol, amount: fromRaw(amount0.toString(), t0.decimals) },
    expectedToken1: { symbol: t1.symbol, amount: fromRaw(amount1.toString(), t1.decimals) },
    remainingLiquidity: updated.liquidity,
  }, null, 2));
}

// ---------------------------------------------------------------------------
// Handler: collect (fees)
// ---------------------------------------------------------------------------
async function handleCollect(tronWeb, opts) {
  const {
    network, execute, checkOnly, positionId, walletAddress,
    token0Info, token1Info, fee, tickLower, tickUpper
  } = opts;

  const v3Cfg = allContracts.v3[network];
  const pmAddr = v3Cfg.positionManager.address;

  // ---- Step 1: Find position -----------------------------------------------
  console.error('📊 Step 1: Finding position...');
  let position, tokenId;
  if (positionId) {
    position = await getPositionOnChain(tronWeb, pmAddr, positionId);
    tokenId = positionId;
  } else {
    const t0Addr = pairAddr(token0Info, network);
    const t1Addr = pairAddr(token1Info, network);
    const found = await findPositionByParams(tronWeb, pmAddr, walletAddress, t0Addr, t1Addr, fee, tickLower, tickUpper);
    if (!found) throw new Error('Position not found');
    position = found; tokenId = found.tokenId;
  }
  console.error(`   Position #${tokenId}`);

  // ---- Step 2: Estimate fees -----------------------------------------------
  console.error('');
  console.error('🔢 Step 2: Estimating claimable fees...');
  const fees = await estimateFees(tronWeb, pmAddr, tokenId, walletAddress);
  const t0 = getTokenInfoByAddress(position.token0, network);
  const t1 = getTokenInfoByAddress(position.token1, network);

  console.error(`   ${t0.symbol}: ${fromRaw(fees.fee0, t0.decimals)}`);
  console.error(`   ${t1.symbol}: ${fromRaw(fees.fee1, t1.decimals)}`);

  if (BigInt(fees.fee0) === 0n && BigInt(fees.fee1) === 0n) {
    console.error('   ⚠️  No claimable fees');
    console.log(JSON.stringify({ action: 'collect', positionId: tokenId, claimable: false }));
    return;
  }

  if (checkOnly) {
    console.log(JSON.stringify({
      action: 'collect', positionId: tokenId, claimable: true,
      fee0: { symbol: t0.symbol, amount: fromRaw(fees.fee0, t0.decimals) },
      fee1: { symbol: t1.symbol, amount: fromRaw(fees.fee1, t1.decimals) },
      readyToExecute: true,
    }, null, 2)); return;
  }

  if (!execute) {
    console.log(JSON.stringify({ dryRun: true, action: 'collect', positionId: tokenId })); return;
  }

  // ---- Step 3: Execute collect ---------------------------------------------
  console.error('\n💱 Step 3: Collecting fees...');
  const pm = await tronWeb.contract(PM_ABI, pmAddr);
  const tx = await pm.collect([tokenId, walletAddress, MAX_UINT128, MAX_UINT128]).send({ feeLimit: 1_000_000_000 });
  console.error(`   ✅ collect tx: ${tx}`);

  const explorerBase = network === 'mainnet' ? 'https://tronscan.org' : 'https://nile.tronscan.org';
  console.log(JSON.stringify({
    success: true, action: 'collect', positionId: tokenId,
    transaction: tx, explorer: `${explorerBase}/#/transaction/${tx}`,
    fee0: { symbol: t0.symbol, amount: fromRaw(fees.fee0, t0.decimals) },
    fee1: { symbol: t1.symbol, amount: fromRaw(fees.fee1, t1.decimals) },
  }, null, 2));
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------
function printUsage() {
  console.error('SunSwap V3 Position Manager');
  console.error('');
  console.error('Usage:');
  console.error('  node position.js positions [--network nile|mainnet]');
  console.error('  node position.js add TOKEN_A TOKEN_B AMT_A AMT_B --fee N --tick-lower N --tick-upper N [OPTIONS]');
  console.error('  node position.js remove [TOKEN_A TOKEN_B --fee N --tick-lower N --tick-upper N | --position-id N] [--percent N] [OPTIONS]');
  console.error('  node position.js collect [TOKEN_A TOKEN_B --fee N --tick-lower N --tick-upper N | --position-id N] [OPTIONS]');
  console.error('');
  console.error('Options:');
  console.error('  --network <nile|mainnet>     Network (default: nile)');
  console.error('  --slippage <5>               Slippage % (default: 5)');
  console.error('  --execute                    Execute on-chain');
  console.error('  --check-only                 Read-only check');
  console.error('  --approve-only               Only approve tokens (requires --execute)');
  console.error('  --create-pool                Create pool if not exist (add only)');
  console.error('  --position-id <N>            Position NFT token ID');
  console.error('  --percent <0-100>            Percentage to remove (default: 100)');
  console.error('');
  console.error('Fee tiers:  100 (0.01%), 500 (0.05%), 3000 (0.3%), 10000 (1%)');
  console.error('');
  console.error('Workflow:');
  console.error('  1. node position.js add TRX USDT 100 15 --fee 3000 --tick-lower -60 --tick-upper 60 --check-only');
  console.error('  2. node position.js add TRX USDT 100 15 --fee 3000 --tick-lower -60 --tick-upper 60 --approve-only --execute');
  console.error('  3. node position.js add TRX USDT 100 15 --fee 3000 --tick-lower -60 --tick-upper 60 --execute');
}

function parseArgs() {
  const args = process.argv.slice(2);
  if (args.length < 1) { printUsage(); process.exit(1); }

  const action = args[0].toLowerCase();
  if (!['positions', 'add', 'remove', 'collect'].includes(action)) {
    console.error(`Unknown action: ${action}. Use positions, add, remove, collect.`);
    process.exit(1);
  }

  let tokenAInput, tokenBInput, amountA, amountB;
  let network = 'nile', slippage = 5, execute = false, checkOnly = false, approveOnly = false;
  let createPool = false, positionId = null, percent = 100;
  let fee = null, tickLower = null, tickUpper = null;

  function parseOpts(opts) {
    for (let i = 0; i < opts.length; i++) {
      const a = opts[i];
      if (a === '--network' && i + 1 < opts.length) network = opts[++i];
      else if (a === '--slippage' && i + 1 < opts.length) slippage = parseFloat(opts[++i]);
      else if (a === '--execute') execute = true;
      else if (a === '--check-only') checkOnly = true;
      else if (a === '--approve-only') approveOnly = true;
      else if (a === '--create-pool') createPool = true;
      else if (a === '--fee' && i + 1 < opts.length) fee = parseInt(opts[++i]);
      else if (a === '--tick-lower' && i + 1 < opts.length) tickLower = parseInt(opts[++i]);
      else if (a === '--tick-upper' && i + 1 < opts.length) tickUpper = parseInt(opts[++i]);
      else if (a === '--position-id' && i + 1 < opts.length) positionId = opts[++i];
      else if (a === '--percent' && i + 1 < opts.length) percent = parseInt(opts[++i]);
    }
  }

  if (action === 'add') {
    if (args.length < 5) { printUsage(); process.exit(1); }
    tokenAInput = args[1]; tokenBInput = args[2]; amountA = args[3]; amountB = args[4];
    parseOpts(args.slice(5));
  } else if (action === 'remove' || action === 'collect') {
    if (args[1] && !args[1].startsWith('--')) {
      tokenAInput = args[1]; tokenBInput = args[2];
      parseOpts(args.slice(3));
    } else {
      parseOpts(args.slice(1));
    }
  } else {
    parseOpts(args.slice(1));
  }

  return {
    action, tokenAInput, tokenBInput, amountA, amountB,
    network, slippage, execute, checkOnly, approveOnly,
    createPool, fee, tickLower, tickUpper, positionId, percent
  };
}

async function main() {
  try {
    const opts = parseArgs();
    console.error(`⚡ SunSwap V3 Position: ${opts.action} on ${opts.network}`);
    console.error('');

    const privateKey = getPrivateKeyOrExit();
    const endpoint = TRON_ENDPOINTS[opts.network];
    const tronWeb = new TronWeb({
      fullHost: endpoint.fullHost,
      headers: endpoint.apiKey ? { 'TRON-PRO-API-KEY': endpoint.apiKey } : {},
      privateKey
    });
    const walletAddress = tronWeb.defaultAddress.base58;
    console.error(`💼 Wallet: ${walletAddress}`);
    console.error('');

    if (opts.action === 'positions') {
      await handlePositions(tronWeb, { network: opts.network, walletAddress });
      return;
    }

    const norm = (s) => (s && s.startsWith('T') && s.length === 34) ? s : (s || '').toUpperCase();

    if (opts.action === 'add') {
      if (opts.fee === null || opts.tickLower === null || opts.tickUpper === null)
        throw new Error('add requires --fee, --tick-lower, --tick-upper');

      const tokenAInfo = getTokenInfo(norm(opts.tokenAInput), opts.network);
      const tokenBInfo = getTokenInfo(norm(opts.tokenBInput), opts.network);
      const { token0Info, token1Info, swapped } = sortTokens(tronWeb, tokenAInfo, tokenBInfo, opts.network);

      const amount0Raw = swapped ? toRaw(opts.amountB, token0Info.decimals) : toRaw(opts.amountA, token0Info.decimals);
      const amount1Raw = swapped ? toRaw(opts.amountA, token1Info.decimals) : toRaw(opts.amountB, token1Info.decimals);

      const tickSpacing = FEE_TICK_SPACING[opts.fee];
      if (!tickSpacing) throw new Error(`Invalid fee: ${opts.fee}. Valid: 100, 500, 3000, 10000`);
      let tl = opts.tickLower, tu = opts.tickUpper;
      if (tl % tickSpacing !== 0) { tl = nearestUsableTick(tl, tickSpacing); console.error(`   ⚠️  tickLower aligned: ${opts.tickLower} → ${tl}`); }
      if (tu % tickSpacing !== 0) { tu = nearestUsableTick(tu, tickSpacing); console.error(`   ⚠️  tickUpper aligned: ${opts.tickUpper} → ${tu}`); }

      await handleAdd(tronWeb, {
        token0Info, token1Info, amount0Raw, amount1Raw,
        fee: opts.fee, tickLower: tl, tickUpper: tu,
        network: opts.network, slippage: opts.slippage,
        execute: opts.execute, checkOnly: opts.checkOnly, approveOnly: opts.approveOnly,
        createPool: opts.createPool, positionId: opts.positionId, walletAddress
      });

    } else if (opts.action === 'remove') {
      if (!opts.positionId && (!opts.tokenAInput || !opts.tokenBInput || opts.fee === null || opts.tickLower === null || opts.tickUpper === null))
        throw new Error('remove requires --position-id or (TOKEN_A TOKEN_B --fee --tick-lower --tick-upper)');

      let token0Info, token1Info;
      if (!opts.positionId) {
        const a = getTokenInfo(norm(opts.tokenAInput), opts.network);
        const b = getTokenInfo(norm(opts.tokenBInput), opts.network);
        ({ token0Info, token1Info } = sortTokens(tronWeb, a, b, opts.network));
      }

      await handleRemove(tronWeb, {
        token0Info, token1Info,
        fee: opts.fee, tickLower: opts.tickLower, tickUpper: opts.tickUpper,
        positionId: opts.positionId, percent: opts.percent,
        network: opts.network, slippage: opts.slippage,
        execute: opts.execute, checkOnly: opts.checkOnly, walletAddress
      });

    } else if (opts.action === 'collect') {
      if (!opts.positionId && (!opts.tokenAInput || !opts.tokenBInput || opts.fee === null || opts.tickLower === null || opts.tickUpper === null))
        throw new Error('collect requires --position-id or (TOKEN_A TOKEN_B --fee --tick-lower --tick-upper)');

      let token0Info, token1Info;
      if (!opts.positionId) {
        const a = getTokenInfo(norm(opts.tokenAInput), opts.network);
        const b = getTokenInfo(norm(opts.tokenBInput), opts.network);
        ({ token0Info, token1Info } = sortTokens(tronWeb, a, b, opts.network));
      }

      await handleCollect(tronWeb, {
        token0Info, token1Info,
        fee: opts.fee, tickLower: opts.tickLower, tickUpper: opts.tickUpper,
        positionId: opts.positionId, network: opts.network,
        execute: opts.execute, checkOnly: opts.checkOnly, walletAddress
      });
    }
  } catch (error) {
    console.error('');
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

if (require.main === module) { main(); }

module.exports = {
  getSqrtRatioAtTick, bigIntSqrt, maxLiquidityForAmounts, getAmountsForLiquidity,
  nearestUsableTick, computeInitialSqrtPriceX96,
  toRaw, fromRaw, applySlippage,
  handlePositions, handleAdd, handleRemove, handleCollect,
};
