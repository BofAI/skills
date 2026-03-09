#!/usr/bin/env node

/**
 * SunSwap V2 Liquidity Management Script
 *
 * Add or remove liquidity on SunSwap V2 pools.
 *
 * Usage:
 *   node liquidity.js add <TOKEN_A> <TOKEN_B> <AMOUNT_A> <AMOUNT_B> [OPTIONS]
 *   node liquidity.js remove <TOKEN_A> <TOKEN_B> <LP_AMOUNT> [OPTIONS]
 *
 * TOKEN_A/TOKEN_B can be token symbol (TRX, USDT) or contract address (T9yD...)
 *
 * Options:
 *   --network <nile|mainnet>    Network (default: nile)
 *   --slippage <5>              Slippage tolerance % (default: 5)
 *   --execute                   Execute tx (without this, dry-run only)
 *   --check-only                Only check balances and allowances (read-only)
 *   --approve-only              Only approve tokens (requires --execute)
 *
 * Workflow (same as swap.js — each private-key step needs explicit --execute):
 *   1. node liquidity.js add TRX USDT 100 15 --check-only        # read-only check
 *   2. node liquidity.js add TRX USDT 100 15 --approve-only --execute  # approve
 *   3. node liquidity.js add TRX USDT 100 15 --execute            # add liquidity
 *
 * Examples:
 *   node liquidity.js add TRX USDT 100 15 --check-only
 *   node liquidity.js add TRX USDT 100 15 --approve-only --execute
 *   node liquidity.js add TRX USDT 100 15 --network nile --execute
 *   node liquidity.js remove TRX USDT 5.5 --check-only
 *   node liquidity.js remove TRX USDT 5.5 --approve-only --execute
 *   node liquidity.js remove TRX USDT 5.5 --network nile --execute
 */

const { TronWeb } = require('tronweb');
const path = require('path');
const fs = require('fs');
const { getPrivateKeyOrExit, sleep } = require('./utils');

// ---------------------------------------------------------------------------
// Resources
// ---------------------------------------------------------------------------
const tokensPath = path.join(__dirname, '../resources/common_tokens.json');
const liqContractsPath = path.join(__dirname, '../resources/liquidity_manager_contracts.json');
const tokens = JSON.parse(fs.readFileSync(tokensPath, 'utf8'));
const liqContracts = JSON.parse(fs.readFileSync(liqContractsPath, 'utf8'));

const TRX_ADDRESS = 'T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb';

const TRON_ENDPOINTS = {
  mainnet: { fullHost: 'https://api.trongrid.io', apiKey: process.env.TRONGRID_API_KEY || '' },
  nile:    { fullHost: 'https://nile.trongrid.io', apiKey: '' }
};

const MAX_UINT256 =
  '115792089237316195423570985008687907853269984665640564039457584007913129639935';

// ---------------------------------------------------------------------------
// ABIs – sourced from liquidity_manager_contracts.json + standard pair ABI
// ---------------------------------------------------------------------------
const v2Abi = liqContracts.v2.abi;

const ROUTER_ABI = [
  v2Abi.addLiquidity,
  v2Abi.addLiquidityETH,
  v2Abi.removeLiquidity,
  v2Abi.removeLiquidityETH,
];

const FACTORY_ABI = [v2Abi.getPair];

const TRC20_ABI = [v2Abi.allowance, v2Abi.balanceOf, v2Abi.approve];

const PAIR_ABI = [
  {
    constant: true, inputs: [], name: 'getReserves',
    outputs: [
      { name: '_reserve0', type: 'uint112' },
      { name: '_reserve1', type: 'uint112' },
      { name: '_blockTimestampLast', type: 'uint32' }
    ],
    type: 'function'
  },
  { constant: true, inputs: [], name: 'token0',
    outputs: [{ name: '', type: 'address' }], type: 'function' },
  { constant: true, inputs: [], name: 'token1',
    outputs: [{ name: '', type: 'address' }], type: 'function' },
  { constant: true, inputs: [], name: 'totalSupply',
    outputs: [{ name: '', type: 'uint256' }], type: 'function' },
  ...TRC20_ABI
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function toRaw(amount, decimals) {
  const parts = amount.toString().split('.');
  const whole = parts[0] || '0';
  let frac = parts[1] || '';
  if (frac.length > decimals) {
    frac = frac.substring(0, decimals);
  } else {
    frac = frac.padEnd(decimals, '0');
  }
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
  const networkTokens = tokens[network];
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

function getWTRXAddress(network) {
  const wtrx = tokens[network].WTRX;
  if (!wtrx) throw new Error(`WTRX not configured for network: ${network}`);
  return wtrx.address;
}

// Determine the on-chain address used for pair lookups (WTRX for TRX)
function pairAddr(tokenInfo, network) {
  return isTRX(tokenInfo) ? getWTRXAddress(network) : tokenInfo.address;
}

// ---------------------------------------------------------------------------
// On-chain reads
// ---------------------------------------------------------------------------

async function getBalance(tronWeb, tokenAddress, wallet) {
  if (tokenAddress === TRX_ADDRESS) {
    return (await tronWeb.trx.getBalance(wallet)).toString();
  }
  const c = await tronWeb.contract(TRC20_ABI, tokenAddress);
  return (await c.balanceOf(wallet).call()).toString();
}

async function getAllowance(tronWeb, tokenAddress, owner, spender) {
  if (tokenAddress === TRX_ADDRESS) return MAX_UINT256;
  const c = await tronWeb.contract(TRC20_ABI, tokenAddress);
  return (await c.allowance(owner, spender).call()).toString();
}

async function approveToken(tronWeb, tokenAddress, spender) {
  console.error(`   📝 Approving ${tokenAddress} for router...`);
  const c = await tronWeb.contract(TRC20_ABI, tokenAddress);
  const tx = await c.approve(spender, MAX_UINT256).send({ feeLimit: 100_000_000 });
  console.error(`   ✅ Approval tx: ${tx}`);
  console.error('   ⏳ Waiting 15 s for confirmation...');
  await sleep(15000);
  return tx;
}

async function getPairInfo(tronWeb, factoryAddress, tokenAddrA, tokenAddrB) {
  const factory = await tronWeb.contract(FACTORY_ABI, factoryAddress);
  const pairHex = await factory.getPair(tokenAddrA, tokenAddrB).call();
  const pairBase58 = tronWeb.address.fromHex(pairHex);

  const ZERO_BASE58 = tronWeb.address.fromHex('410000000000000000000000000000000000000000');
  if (!pairBase58 || pairBase58 === ZERO_BASE58) {
    return { pairAddress: null, reserve0: '0', reserve1: '0',
             token0: null, token1: null, totalSupply: '0' };
  }

  const pair = await tronWeb.contract(PAIR_ABI, pairBase58);
  const reserves = await pair.getReserves().call();
  const token0Hex = await pair.token0().call();
  const token1Hex = await pair.token1().call();
  const totalSupply = await pair.totalSupply().call();

  return {
    pairAddress: pairBase58,
    reserve0: (reserves._reserve0 ?? reserves[0]).toString(),
    reserve1: (reserves._reserve1 ?? reserves[1]).toString(),
    token0: tronWeb.address.fromHex(token0Hex),
    token1: tronWeb.address.fromHex(token1Hex),
    totalSupply: totalSupply.toString()
  };
}

// ---------------------------------------------------------------------------
// Core logic
// ---------------------------------------------------------------------------

/**
 * Given desired amounts and current reserves, compute the actual amounts that
 * maintain the pool ratio (Uniswap V2 _addLiquidity algorithm).
 */
function computeOptimalAmounts(amountADesired, amountBDesired, reserveA, reserveB) {
  const rA = BigInt(reserveA);
  const rB = BigInt(reserveB);
  const dA = BigInt(amountADesired);
  const dB = BigInt(amountBDesired);

  if (rA === 0n && rB === 0n) {
    return { amountA: amountADesired, amountB: amountBDesired, adjusted: false };
  }

  const optimalB = dA * rB / rA;
  if (optimalB <= dB) {
    return { amountA: amountADesired, amountB: optimalB.toString(), adjusted: optimalB.toString() !== amountBDesired };
  }

  const optimalA = dB * rA / rB;
  return { amountA: optimalA.toString(), amountB: amountBDesired, adjusted: optimalA.toString() !== amountADesired };
}

// ---------------------------------------------------------------------------
// Add Liquidity
// ---------------------------------------------------------------------------

async function handleAddLiquidity(tronWeb, opts) {
  const {
    tokenAInfo, tokenBInfo, amountARaw, amountBRaw,
    network, slippage, execute, checkOnly, approveOnly, walletAddress
  } = opts;

  const v2Cfg = liqContracts.v2[network];
  const routerAddress = v2Cfg.smartRouter.address;
  const factoryAddress = v2Cfg.factory.address;

  const hasTRX = isTRX(tokenAInfo) || isTRX(tokenBInfo);
  const pairTokenA = pairAddr(tokenAInfo, network);
  const pairTokenB = pairAddr(tokenBInfo, network);

  // ---- Step 1: Reserves ---------------------------------------------------
  console.error('📊 Step 1: Checking pool reserves...');
  const pairInfo = await getPairInfo(tronWeb, factoryAddress, pairTokenA, pairTokenB);

  let reserveA = '0';
  let reserveB = '0';

  if (pairInfo.pairAddress) {
    if (pairInfo.token0 === pairTokenA) {
      reserveA = pairInfo.reserve0; reserveB = pairInfo.reserve1;
    } else {
      reserveA = pairInfo.reserve1; reserveB = pairInfo.reserve0;
    }
    console.error(`   Pair: ${pairInfo.pairAddress}`);
    console.error(`   Reserve ${tokenAInfo.symbol}: ${fromRaw(reserveA, tokenAInfo.decimals)}`);
    console.error(`   Reserve ${tokenBInfo.symbol}: ${fromRaw(reserveB, tokenBInfo.decimals)}`);
    console.error(`   LP Total Supply: ${fromRaw(pairInfo.totalSupply, 18)}`);
  } else {
    console.error('   ⚠️  Pool does not exist yet — will create a new pool.');
  }

  // ---- Step 2: Optimal amounts --------------------------------------------
  console.error('');
  console.error('🔢 Step 2: Computing optimal amounts...');

  const optimal = computeOptimalAmounts(amountARaw, amountBRaw, reserveA, reserveB);
  const actualA = optimal.amountA;
  const actualB = optimal.amountB;

  console.error(`   ${tokenAInfo.symbol}: ${fromRaw(amountARaw, tokenAInfo.decimals)} → ${fromRaw(actualA, tokenAInfo.decimals)}`);
  console.error(`   ${tokenBInfo.symbol}: ${fromRaw(amountBRaw, tokenBInfo.decimals)} → ${fromRaw(actualB, tokenBInfo.decimals)}`);

  const unusedTokens = [];
  if (optimal.adjusted) {
    const diffA = BigInt(amountARaw) - BigInt(actualA);
    const diffB = BigInt(amountBRaw) - BigInt(actualB);
    if (diffA > 0n) {
      unusedTokens.push({ symbol: tokenAInfo.symbol, amount: fromRaw(diffA.toString(), tokenAInfo.decimals) });
      console.error(`   ⚠️  Unused ${tokenAInfo.symbol}: ${fromRaw(diffA.toString(), tokenAInfo.decimals)}`);
    }
    if (diffB > 0n) {
      unusedTokens.push({ symbol: tokenBInfo.symbol, amount: fromRaw(diffB.toString(), tokenBInfo.decimals) });
      console.error(`   ⚠️  Unused ${tokenBInfo.symbol}: ${fromRaw(diffB.toString(), tokenBInfo.decimals)}`);
    }
  }

  // ---- Step 3: Balances ---------------------------------------------------
  console.error('');
  console.error('💰 Step 3: Checking balances...');

  const balA = await getBalance(tronWeb, tokenAInfo.address, walletAddress);
  const balB = await getBalance(tronWeb, tokenBInfo.address, walletAddress);
  console.error(`   ${tokenAInfo.symbol}: ${fromRaw(balA, tokenAInfo.decimals)} (need ${fromRaw(actualA, tokenAInfo.decimals)})`);
  console.error(`   ${tokenBInfo.symbol}: ${fromRaw(balB, tokenBInfo.decimals)} (need ${fromRaw(actualB, tokenBInfo.decimals)})`);

  if (BigInt(balA) < BigInt(actualA)) throw new Error(`Insufficient ${tokenAInfo.symbol} balance`);
  if (BigInt(balB) < BigInt(actualB)) throw new Error(`Insufficient ${tokenBInfo.symbol} balance`);

  // ---- Step 4: Approvals --------------------------------------------------
  console.error('');
  console.error('🔐 Step 4: Checking approvals...');

  const pendingApprovals = [];

  if (hasTRX) {
    const other = isTRX(tokenAInfo) ? tokenBInfo : tokenAInfo;
    const otherAmt = isTRX(tokenAInfo) ? actualB : actualA;
    const allowance = await getAllowance(tronWeb, other.address, walletAddress, routerAddress);
    if (BigInt(allowance) < BigInt(otherAmt)) {
      console.error(`   ${other.symbol}: allowance insufficient ❌`);
      pendingApprovals.push(other);
    } else {
      console.error(`   ${other.symbol}: allowance OK ✅`);
    }
    console.error('   TRX: no approval needed ✅');
  } else {
    for (const [info, amt] of [[tokenAInfo, actualA], [tokenBInfo, actualB]]) {
      const allowance = await getAllowance(tronWeb, info.address, walletAddress, routerAddress);
      if (BigInt(allowance) < BigInt(amt)) {
        console.error(`   ${info.symbol}: allowance insufficient ❌`);
        pendingApprovals.push(info);
      } else {
        console.error(`   ${info.symbol}: allowance OK ✅`);
      }
    }
  }

  // ---- --check-only: exit after read-only checks --------------------------
  if (checkOnly) {
    console.error('');
    console.error('✅ Check complete (--check-only mode)');
    const result = {
      action: 'addLiquidity',
      pool: pairInfo.pairAddress,
      tokenA: { symbol: tokenAInfo.symbol, balance: fromRaw(balA, tokenAInfo.decimals), desired: fromRaw(amountARaw, tokenAInfo.decimals), optimal: fromRaw(actualA, tokenAInfo.decimals) },
      tokenB: { symbol: tokenBInfo.symbol, balance: fromRaw(balB, tokenBInfo.decimals), desired: fromRaw(amountBRaw, tokenBInfo.decimals), optimal: fromRaw(actualB, tokenBInfo.decimals) },
      unusedTokens,
      needsApproval: pendingApprovals.map(t => t.symbol),
      readyToExecute: pendingApprovals.length === 0
    };
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  // ---- --approve-only: only approve, then exit ----------------------------
  if (approveOnly) {
    if (pendingApprovals.length === 0) {
      console.error('');
      console.error('✅ All tokens already approved — no action needed.');
      const result = { approved: [], message: 'All tokens already have sufficient allowance' };
      console.log(JSON.stringify(result, null, 2));
      return;
    }
    if (!execute) {
      console.error('');
      console.error('   ⚠️  DRY RUN: would approve ' + pendingApprovals.map(t => t.symbol).join(', ') + ' (use --execute)');
      const result = { dryRun: true, action: 'approve', tokens: pendingApprovals.map(t => t.symbol) };
      console.log(JSON.stringify(result, null, 2));
      return;
    }
    const approvedTxs = [];
    for (const t of pendingApprovals) {
      const tx = await approveToken(tronWeb, t.address, routerAddress);
      approvedTxs.push({ symbol: t.symbol, transaction: tx });
    }
    console.error('');
    console.error('✅ Approval complete. Re-run with --execute (without --approve-only) to add liquidity.');
    const result = { approved: approvedTxs };
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  // ---- --execute: add liquidity (will NOT auto-approve) --------------------
  if (pendingApprovals.length > 0) {
    console.error('');
    console.error('🚨 Approval required before adding liquidity!');
    console.error(`   Tokens needing approval: ${pendingApprovals.map(t => t.symbol).join(', ')}`);
    console.error('');
    console.error('   Run --approve-only --execute first to approve.');
    const result = {
      action: 'addLiquidity',
      status: 'approval_required',
      needsApproval: pendingApprovals.map(t => t.symbol),
      pool: pairInfo.pairAddress,
      tokenA: { symbol: tokenAInfo.symbol, desired: fromRaw(amountARaw, tokenAInfo.decimals), optimal: fromRaw(actualA, tokenAInfo.decimals) },
      tokenB: { symbol: tokenBInfo.symbol, desired: fromRaw(amountBRaw, tokenBInfo.decimals), optimal: fromRaw(actualB, tokenBInfo.decimals) },
      unusedTokens
    };
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  // LP balance before
  let lpBefore = '0';
  if (pairInfo.pairAddress) {
    lpBefore = await getBalance(tronWeb, pairInfo.pairAddress, walletAddress);
  }

  // ---- Step 5: Execute ----------------------------------------------------
  console.error('');
  console.error('💱 Step 5: Adding liquidity...');

  const amountAMin = applySlippage(actualA, slippage);
  const amountBMin = applySlippage(actualB, slippage);
  const deadline = Math.floor(Date.now() / 1000) + 300;

  if (!execute) {
    console.error('   ⚠️  DRY RUN (use --execute to proceed)');
    const result = {
      dryRun: true, action: 'addLiquidity',
      pool: pairInfo.pairAddress,
      method: hasTRX ? 'addLiquidityETH' : 'addLiquidity',
      tokenA: { symbol: tokenAInfo.symbol, desired: fromRaw(amountARaw, tokenAInfo.decimals), optimal: fromRaw(actualA, tokenAInfo.decimals) },
      tokenB: { symbol: tokenBInfo.symbol, desired: fromRaw(amountBRaw, tokenBInfo.decimals), optimal: fromRaw(actualB, tokenBInfo.decimals) },
      unusedTokens,
      needsApproval: [],
      hasTRX
    };
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  const router = await tronWeb.contract(ROUTER_ABI, routerAddress);
  let tx;

  if (hasTRX) {
    const otherToken = isTRX(tokenAInfo) ? tokenBInfo : tokenAInfo;
    const otherAmount = isTRX(tokenAInfo) ? actualB : actualA;
    const otherMin    = isTRX(tokenAInfo) ? amountBMin : amountAMin;
    const trxAmount   = isTRX(tokenAInfo) ? actualA : actualB;
    const trxMin      = isTRX(tokenAInfo) ? amountAMin : amountBMin;

    console.error(`   addLiquidityETH(${otherToken.symbol} ${fromRaw(otherAmount, otherToken.decimals)}, TRX ${fromRaw(trxAmount, 6)})...`);
    tx = await router.addLiquidityETH(
      otherToken.address, otherAmount, otherMin, trxMin, walletAddress, deadline
    ).send({ feeLimit: 1_000_000_000, callValue: trxAmount });
  } else {
    console.error(`   addLiquidity(${tokenAInfo.symbol} ${fromRaw(actualA, tokenAInfo.decimals)}, ${tokenBInfo.symbol} ${fromRaw(actualB, tokenBInfo.decimals)})...`);
    tx = await router.addLiquidity(
      tokenAInfo.address, tokenBInfo.address,
      actualA, actualB, amountAMin, amountBMin,
      walletAddress, deadline
    ).send({ feeLimit: 1_000_000_000 });
  }

  console.error(`   ✅ Tx: ${tx}`);

  // ---- Step 6: Post-check -------------------------------------------------
  console.error('');
  console.error('📊 Step 6: Checking results...');
  await sleep(5000);

  const pairAfter = await getPairInfo(tronWeb, factoryAddress, pairTokenA, pairTokenB);
  const lpAfter = pairAfter.pairAddress
    ? await getBalance(tronWeb, pairAfter.pairAddress, walletAddress)
    : '0';
  const lpGain = (BigInt(lpAfter) - BigInt(lpBefore)).toString();

  console.error(`   LP Token: ${pairAfter.pairAddress}`);
  console.error(`   LP Before: ${fromRaw(lpBefore, 18)}`);
  console.error(`   LP After:  ${fromRaw(lpAfter, 18)}`);
  console.error(`   LP Gained: ${fromRaw(lpGain, 18)}`);

  // Report actual usage via balance diff (skip TRX — includes gas)
  const balAAfter = await getBalance(tronWeb, tokenAInfo.address, walletAddress);
  const balBAfter = await getBalance(tronWeb, tokenBInfo.address, walletAddress);

  if (!isTRX(tokenAInfo)) {
    const used = BigInt(balA) - BigInt(balAAfter);
    const returned = BigInt(actualA) - used;
    if (returned > 0n) {
      console.error(`   ⚠️  ${tokenAInfo.symbol} returned: ${fromRaw(returned.toString(), tokenAInfo.decimals)}`);
    }
  }
  if (!isTRX(tokenBInfo)) {
    const used = BigInt(balB) - BigInt(balBAfter);
    const returned = BigInt(actualB) - used;
    if (returned > 0n) {
      console.error(`   ⚠️  ${tokenBInfo.symbol} returned: ${fromRaw(returned.toString(), tokenBInfo.decimals)}`);
    }
  }

  const explorerBase = network === 'mainnet' ? 'https://tronscan.org' : 'https://nile.tronscan.org';
  const result = {
    success: true, action: 'addLiquidity', transaction: tx,
    explorer: `${explorerBase}/#/transaction/${tx}`,
    pool: pairAfter.pairAddress,
    lpGained: fromRaw(lpGain, 18),
    tokenA: { symbol: tokenAInfo.symbol, input: fromRaw(actualA, tokenAInfo.decimals) },
    tokenB: { symbol: tokenBInfo.symbol, input: fromRaw(actualB, tokenBInfo.decimals) },
    unusedTokens
  };
  console.log(JSON.stringify(result, null, 2));
}

// ---------------------------------------------------------------------------
// Remove Liquidity
// ---------------------------------------------------------------------------

async function handleRemoveLiquidity(tronWeb, opts) {
  const {
    tokenAInfo, tokenBInfo, lpAmountRaw,
    network, slippage, execute, checkOnly, approveOnly, walletAddress
  } = opts;

  const v2Cfg = liqContracts.v2[network];
  const routerAddress = v2Cfg.smartRouter.address;
  const factoryAddress = v2Cfg.factory.address;

  const hasTRX = isTRX(tokenAInfo) || isTRX(tokenBInfo);
  const pairTokenA = pairAddr(tokenAInfo, network);
  const pairTokenB = pairAddr(tokenBInfo, network);

  // ---- Step 1: Pair info --------------------------------------------------
  console.error('📊 Step 1: Getting pool info...');
  const pairInfo = await getPairInfo(tronWeb, factoryAddress, pairTokenA, pairTokenB);

  if (!pairInfo.pairAddress) throw new Error('Pool does not exist for this token pair');

  let reserveA, reserveB;
  if (pairInfo.token0 === pairTokenA) {
    reserveA = pairInfo.reserve0; reserveB = pairInfo.reserve1;
  } else {
    reserveA = pairInfo.reserve1; reserveB = pairInfo.reserve0;
  }

  console.error(`   Pair: ${pairInfo.pairAddress}`);
  console.error(`   Reserve ${tokenAInfo.symbol}: ${fromRaw(reserveA, tokenAInfo.decimals)}`);
  console.error(`   Reserve ${tokenBInfo.symbol}: ${fromRaw(reserveB, tokenBInfo.decimals)}`);
  console.error(`   LP Total Supply: ${fromRaw(pairInfo.totalSupply, 18)}`);

  const lpBalance = await getBalance(tronWeb, pairInfo.pairAddress, walletAddress);
  console.error(`   Your LP Balance: ${fromRaw(lpBalance, 18)}`);

  if (BigInt(lpBalance) < BigInt(lpAmountRaw)) {
    throw new Error(`Insufficient LP balance. Have: ${fromRaw(lpBalance, 18)}, Need: ${fromRaw(lpAmountRaw, 18)}`);
  }

  // ---- Step 2: Expected output --------------------------------------------
  console.error('');
  console.error('🔢 Step 2: Expected token output...');

  const totalSupply = BigInt(pairInfo.totalSupply);
  const lpBig = BigInt(lpAmountRaw);
  const expectedA = (lpBig * BigInt(reserveA) / totalSupply).toString();
  const expectedB = (lpBig * BigInt(reserveB) / totalSupply).toString();

  console.error(`   ${tokenAInfo.symbol}: ~${fromRaw(expectedA, tokenAInfo.decimals)}`);
  console.error(`   ${tokenBInfo.symbol}: ~${fromRaw(expectedB, tokenBInfo.decimals)}`);

  // ---- Step 3: LP approval ------------------------------------------------
  console.error('');
  console.error('🔐 Step 3: Checking LP token approval...');

  const lpAllowance = await getAllowance(tronWeb, pairInfo.pairAddress, walletAddress, routerAddress);
  const needsApproval = BigInt(lpAllowance) < BigInt(lpAmountRaw);

  if (needsApproval) {
    console.error('   LP allowance insufficient ❌');
  } else {
    console.error('   LP allowance OK ✅');
  }

  // ---- --check-only: exit after read-only checks --------------------------
  if (checkOnly) {
    console.error('');
    console.error('✅ Check complete (--check-only mode)');
    const result = {
      action: 'removeLiquidity',
      pool: pairInfo.pairAddress,
      lpBalance: fromRaw(lpBalance, 18),
      lpToRemove: fromRaw(lpAmountRaw, 18),
      expectedTokenA: { symbol: tokenAInfo.symbol, amount: fromRaw(expectedA, tokenAInfo.decimals) },
      expectedTokenB: { symbol: tokenBInfo.symbol, amount: fromRaw(expectedB, tokenBInfo.decimals) },
      needsApproval: needsApproval ? ['LP'] : [],
      readyToExecute: !needsApproval
    };
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  // ---- --approve-only: only approve LP, then exit -------------------------
  if (approveOnly) {
    if (!needsApproval) {
      console.error('');
      console.error('✅ LP token already approved — no action needed.');
      const result = { approved: [], message: 'LP token already has sufficient allowance' };
      console.log(JSON.stringify(result, null, 2));
      return;
    }
    if (!execute) {
      console.error('');
      console.error('   ⚠️  DRY RUN: would approve LP token (use --execute)');
      const result = { dryRun: true, action: 'approve', tokens: ['LP'] };
      console.log(JSON.stringify(result, null, 2));
      return;
    }
    const tx = await approveToken(tronWeb, pairInfo.pairAddress, routerAddress);
    console.error('');
    console.error('✅ LP approval complete. Re-run with --execute (without --approve-only) to remove liquidity.');
    const result = { approved: [{ symbol: 'LP', address: pairInfo.pairAddress, transaction: tx }] };
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  // ---- --execute: remove liquidity (will NOT auto-approve) -----------------
  if (needsApproval) {
    console.error('');
    console.error('🚨 LP token approval required before removing liquidity!');
    console.error('');
    console.error('   Run --approve-only --execute first to approve.');
    const result = {
      action: 'removeLiquidity',
      status: 'approval_required',
      needsApproval: ['LP'],
      pool: pairInfo.pairAddress,
      lpAmount: fromRaw(lpAmountRaw, 18),
      expectedTokenA: { symbol: tokenAInfo.symbol, amount: fromRaw(expectedA, tokenAInfo.decimals) },
      expectedTokenB: { symbol: tokenBInfo.symbol, amount: fromRaw(expectedB, tokenBInfo.decimals) }
    };
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  // ---- Step 4: Execute ----------------------------------------------------
  console.error('');
  console.error('💱 Step 4: Removing liquidity...');

  const amountAMin = applySlippage(expectedA, slippage);
  const amountBMin = applySlippage(expectedB, slippage);
  const deadline = Math.floor(Date.now() / 1000) + 300;

  if (!execute) {
    console.error('   ⚠️  DRY RUN (use --execute to proceed)');
    const result = {
      dryRun: true, action: 'removeLiquidity',
      pool: pairInfo.pairAddress,
      method: hasTRX ? 'removeLiquidityETH' : 'removeLiquidity',
      lpAmount: fromRaw(lpAmountRaw, 18),
      expectedTokenA: { symbol: tokenAInfo.symbol, amount: fromRaw(expectedA, tokenAInfo.decimals) },
      expectedTokenB: { symbol: tokenBInfo.symbol, amount: fromRaw(expectedB, tokenBInfo.decimals) },
      needsApproval: false, hasTRX
    };
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  const router = await tronWeb.contract(ROUTER_ABI, routerAddress);
  let tx;

  if (hasTRX) {
    const otherToken = isTRX(tokenAInfo) ? tokenBInfo : tokenAInfo;
    const otherMin   = isTRX(tokenAInfo) ? amountBMin : amountAMin;
    const trxMin     = isTRX(tokenAInfo) ? amountAMin : amountBMin;

    console.error(`   removeLiquidityETH(${otherToken.symbol}, LP ${fromRaw(lpAmountRaw, 18)})...`);
    tx = await router.removeLiquidityETH(
      otherToken.address, lpAmountRaw, otherMin, trxMin, walletAddress, deadline
    ).send({ feeLimit: 1_000_000_000 });
  } else {
    console.error(`   removeLiquidity(${tokenAInfo.symbol}, ${tokenBInfo.symbol}, LP ${fromRaw(lpAmountRaw, 18)})...`);
    tx = await router.removeLiquidity(
      tokenAInfo.address, tokenBInfo.address,
      lpAmountRaw, amountAMin, amountBMin,
      walletAddress, deadline
    ).send({ feeLimit: 1_000_000_000 });
  }

  console.error(`   ✅ Tx: ${tx}`);

  // ---- Step 5: Post-check -------------------------------------------------
  console.error('');
  console.error('📊 Step 5: Checking results...');
  await sleep(5000);

  const lpAfter = await getBalance(tronWeb, pairInfo.pairAddress, walletAddress);
  console.error(`   LP Remaining: ${fromRaw(lpAfter, 18)}`);

  const explorerBase = network === 'mainnet' ? 'https://tronscan.org' : 'https://nile.tronscan.org';
  const result = {
    success: true, action: 'removeLiquidity', transaction: tx,
    explorer: `${explorerBase}/#/transaction/${tx}`,
    pool: pairInfo.pairAddress,
    lpRemoved: fromRaw(lpAmountRaw, 18),
    lpRemaining: fromRaw(lpAfter, 18),
    expectedTokenA: { symbol: tokenAInfo.symbol, amount: fromRaw(expectedA, tokenAInfo.decimals) },
    expectedTokenB: { symbol: tokenBInfo.symbol, amount: fromRaw(expectedB, tokenBInfo.decimals) }
  };
  console.log(JSON.stringify(result, null, 2));
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function printUsage() {
  console.error('SunSwap V2 Liquidity Manager');
  console.error('');
  console.error('Usage:');
  console.error('  node liquidity.js add <TOKEN_A> <TOKEN_B> <AMOUNT_A> <AMOUNT_B> [OPTIONS]');
  console.error('  node liquidity.js remove <TOKEN_A> <TOKEN_B> <LP_AMOUNT> [OPTIONS]');
  console.error('');
  console.error('Options:');
  console.error('  --network <nile|mainnet>    Network (default: nile)');
  console.error('  --slippage <5>              Slippage % (default: 5)');
  console.error('  --execute                   Execute (without this, dry-run)');
  console.error('  --check-only                Only check balances & allowances (read-only)');
  console.error('  --approve-only              Only approve tokens (requires --execute)');
  console.error('');
  console.error('Step-by-step workflow:');
  console.error('  1. node liquidity.js add TRX USDT 100 15 --check-only');
  console.error('  2. node liquidity.js add TRX USDT 100 15 --approve-only --execute');
  console.error('  3. node liquidity.js add TRX USDT 100 15 --execute');
}

function parseArgs() {
  const args = process.argv.slice(2);
  if (args.length < 4) { printUsage(); process.exit(1); }

  const action = args[0].toLowerCase();
  if (action !== 'add' && action !== 'remove') {
    console.error(`Unknown action: ${action}. Use "add" or "remove".`);
    process.exit(1);
  }

  const tokenAInput = (args[1].startsWith('T') && args[1].length === 34) ? args[1] : args[1].toUpperCase();
  const tokenBInput = (args[2].startsWith('T') && args[2].length === 34) ? args[2] : args[2].toUpperCase();

  let amountA, amountB, lpAmount;
  let optStart;

  if (action === 'add') {
    if (args.length < 5) {
      console.error('Add requires: add <TOKEN_A> <TOKEN_B> <AMOUNT_A> <AMOUNT_B>');
      process.exit(1);
    }
    amountA = args[3]; amountB = args[4]; optStart = 5;
  } else {
    lpAmount = args[3]; optStart = 4;
  }

  let network = 'nile', slippage = 5, execute = false, checkOnly = false, approveOnly = false;
  for (let i = optStart; i < args.length; i++) {
    if (args[i] === '--network' && i + 1 < args.length) network = args[++i];
    else if (args[i] === '--slippage' && i + 1 < args.length) slippage = parseFloat(args[++i]);
    else if (args[i] === '--execute') execute = true;
    else if (args[i] === '--check-only') checkOnly = true;
    else if (args[i] === '--approve-only') approveOnly = true;
  }

  return { action, tokenAInput, tokenBInput, amountA, amountB, lpAmount, network, slippage, execute, checkOnly, approveOnly };
}

async function main() {
  try {
    const opts = parseArgs();
    const { action, tokenAInput, tokenBInput, amountA, amountB, lpAmount, network, slippage, execute, checkOnly, approveOnly } = opts;

    console.error(`🌊 SunSwap V2 Liquidity: ${action} on ${network}`);
    console.error('');

    const privateKey = getPrivateKeyOrExit();
    const endpoint = TRON_ENDPOINTS[network];
    const tronWeb = new TronWeb({
      fullHost: endpoint.fullHost,
      headers: endpoint.apiKey ? { 'TRON-PRO-API-KEY': endpoint.apiKey } : {},
      privateKey
    });
    const walletAddress = tronWeb.defaultAddress.base58;
    console.error(`💼 Wallet: ${walletAddress}`);
    console.error('');

    const tokenAInfo = getTokenInfo(tokenAInput, network);
    const tokenBInfo = getTokenInfo(tokenBInput, network);

    if (action === 'add') {
      await handleAddLiquidity(tronWeb, {
        tokenAInfo, tokenBInfo,
        amountARaw: toRaw(amountA, tokenAInfo.decimals),
        amountBRaw: toRaw(amountB, tokenBInfo.decimals),
        network, slippage, execute, checkOnly, approveOnly, walletAddress
      });
    } else {
      await handleRemoveLiquidity(tronWeb, {
        tokenAInfo, tokenBInfo,
        lpAmountRaw: toRaw(lpAmount, 18),
        network, slippage, execute, checkOnly, approveOnly, walletAddress
      });
    }
  } catch (error) {
    console.error('');
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  handleAddLiquidity, handleRemoveLiquidity,
  getPairInfo, computeOptimalAmounts,
  toRaw, fromRaw, applySlippage
};
