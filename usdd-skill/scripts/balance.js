#!/usr/bin/env node

/**
 * balance.js — Check USDD, USDT, USDC, JST, and TRX balances.
 *
 * Usage:
 *   node balance.js [--address <wallet>]
 *
 * Examples:
 *   node balance.js
 *   node balance.js --address TXYzL2gqz5AB4dbGeiX9h8unkKHxuWwb
 */

const { CONTRACTS, getTronWeb, getTronWebReadOnly, getNetwork, fromSun, outputJSON, log } = require("./utils");

async function main() {
  const args = process.argv.slice(2);

  // Parse --address flag
  let address = null;
  const addrIdx = args.indexOf("--address");
  if (addrIdx !== -1 && addrIdx + 1 < args.length) {
    address = args[addrIdx + 1];
  }

  let tronWeb;
  if (address) {
    tronWeb = getTronWebReadOnly();
  } else {
    tronWeb = getTronWeb();
    address = tronWeb.defaultAddress.base58;
  }

  const network = getNetwork();
  const tokens = CONTRACTS.tokens[network];
  if (!tokens) throw new Error(`No tokens configured for network "${network}".`);

  log(`Checking balances for ${address} on ${network} ...`);

  const balances = [];

  for (const token of Object.values(tokens)) {
    try {
      if (token.is_native) {
        // TRX: use native balance query
        const rawBalance = await tronWeb.trx.getBalance(address);
        balances.push({
          symbol: token.symbol,
          balance: fromSun(rawBalance, token.decimals),
          address: null,
        });
      } else {
        // TRC20: use balanceOf
        const contract = await tronWeb.contract(
          [CONTRACTS.abi.trc20.balanceOf],
          token.address
        );
        const rawBalance = await contract.balanceOf(address).call();
        balances.push({
          symbol: token.symbol,
          balance: fromSun(BigInt(rawBalance), token.decimals),
          address: token.address,
        });
      }
    } catch (e) {
      balances.push({
        symbol: token.symbol,
        balance: "0",
        address: token.address || null,
        error: e.message,
      });
    }
    // Avoid rate-limiting on TronGrid free tier
    await new Promise((r) => setTimeout(r, 300));
  }

  outputJSON({ wallet: address, network, balances });
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
