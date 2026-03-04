#!/usr/bin/env node

/**
 * balance.js — Check TRC20 token balances (single or batch).
 *
 * Usage:
 *   node balance.js <tokenAddressOrSymbol> [walletAddress]
 *   node balance.js --batch <token1,token2,...> [walletAddress]
 *
 * Environment:
 *   TRON_PRIVATE_KEY, TRON_NETWORK (mainnet|nile), TRONGRID_API_KEY (optional)
 */

const { TRC20_ABI, getTronWeb, resolveToken, fromSun, outputJSON, log } = require("./utils");

async function getTokenBalance(tronWeb, tokenAddress, walletAddress) {
  const contract = await tronWeb.contract(TRC20_ABI, tokenAddress);
  const [balance, decimals, symbol] = await Promise.all([
    contract.balanceOf(walletAddress).call(),
    contract.decimals().call(),
    contract.symbol().call(),
  ]);
  const dec = Number(decimals);
  return {
    token: tokenAddress,
    symbol: String(symbol),
    decimals: dec,
    balance: fromSun(balance, dec),
    balance_raw: String(balance),
  };
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) { console.error("Usage: node balance.js <token> [wallet] OR --batch <t1,t2,...> [wallet]"); process.exit(1); }

  const tronWeb = getTronWeb();
  const isBatch = args[0] === "--batch";

  let walletAddress;
  let tokens;

  if (isBatch) {
    tokens = args[1].split(",").map((t) => resolveToken(t.trim()));
    walletAddress = args[2] || tronWeb.defaultAddress.base58;
  } else {
    tokens = [resolveToken(args[0])];
    walletAddress = args[1] || tronWeb.defaultAddress.base58;
  }

  log(`Checking balances for ${walletAddress} ...`);

  const trxBalance = await tronWeb.trx.getBalance(walletAddress);
  const results = [];
  for (const token of tokens) {
    try {
      results.push(await getTokenBalance(tronWeb, token, walletAddress));
    } catch (e) {
      results.push({ token, error: e.message });
    }
  }

  outputJSON({
    wallet: walletAddress,
    trx_balance: fromSun(trxBalance, 6),
    trx_balance_raw: String(trxBalance),
    tokens: results,
  });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
