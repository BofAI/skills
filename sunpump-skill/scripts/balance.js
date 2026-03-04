#!/usr/bin/env node

/**
 * balance.js — Check TRX and SunPump token balances.
 *
 * Usage:
 *   node balance.js                          # TRX balance of configured wallet
 *   node balance.js <tokenAddress>           # token balance of configured wallet
 *   node balance.js <tokenAddress> <wallet>  # token balance of specified wallet
 *
 * Environment:
 *   TRON_PRIVATE_KEY   — wallet private key (required)
 *   TRON_NETWORK       — mainnet (default) | nile
 *   TRONGRID_API_KEY   — optional TronGrid API key
 */

const {
  CONTRACTS,
  TOKEN_DECIMALS,
  TRX_DECIMALS,
  getTronWeb,
  getLauncherAddress,
  fromSun,
  outputJSON,
  log,
} = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  const tronWeb = getTronWeb();
  const walletAddress =
    args[1] || tronWeb.defaultAddress.base58;

  log(`Checking balances for ${walletAddress} ...`);

  // TRX balance
  const trxBalanceSun = await tronWeb.trx.getBalance(walletAddress);
  const result = {
    wallet: walletAddress,
    trx_balance: fromSun(trxBalanceSun, TRX_DECIMALS),
    trx_balance_raw: String(trxBalanceSun),
  };

  // Token balance (if specified)
  if (args[0]) {
    const tokenAddress = args[0];
    const tokenContract = await tronWeb.contract(
      [CONTRACTS.abi.balanceOf],
      tokenAddress
    );
    const tokenBalance = await tokenContract.balanceOf(walletAddress).call();
    result.token = tokenAddress;
    result.token_balance = fromSun(tokenBalance, TOKEN_DECIMALS);
    result.token_balance_raw = String(tokenBalance);

    // Check allowance to SunPump
    const launcherAddr = getLauncherAddress();
    const allowanceContract = await tronWeb.contract(
      [CONTRACTS.abi.allowance],
      tokenAddress
    );
    const allowance = await allowanceContract
      .allowance(walletAddress, launcherAddr)
      .call();
    result.sunpump_allowance_raw = String(allowance);
    result.sunpump_approved = BigInt(allowance) > 0n;

    log(
      `Token balance: ${result.token_balance} | Approved for SunPump: ${result.sunpump_approved}`
    );
  }

  log(`TRX balance: ${result.trx_balance} TRX`);
  outputJSON(result);
}

main().catch((err) => {
  outputJSON({ error: err.message });
  process.exit(1);
});
