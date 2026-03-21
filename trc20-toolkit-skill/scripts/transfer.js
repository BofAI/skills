#!/usr/bin/env node

/**
 * transfer.js — Transfer TRC20 tokens.
 *
 * Usage:
 *   node transfer.js <tokenAddressOrSymbol> <toAddress> <amount> [--dry-run]
 *
 * Environment:
 *   TRON_PRIVATE_KEY, TRON_NETWORK (mainnet|nile), TRONGRID_API_KEY (optional)
 */

const { TRC20_ABI, getTronWeb, resolveToken, toSun, fromSun, outputJSON, log } = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 3) { console.error("Usage: node transfer.js <token> <toAddress> <amount> [--dry-run]"); process.exit(1); }

  const tronWeb = getTronWeb();
  const tokenAddress = resolveToken(args[0]);
  const toAddress = args[1];
  const amountHuman = args[2];
  const dryRun = args.includes("--dry-run");
  const walletAddress = tronWeb.defaultAddress.base58;

  if (toAddress === walletAddress) {
    outputJSON({ error: "Cannot transfer to yourself." });
    process.exit(1);
  }

  const contract = await tronWeb.contract(TRC20_ABI, tokenAddress);
  const [decimals, symbol, balance] = await Promise.all([
    contract.decimals().call(),
    contract.symbol().call(),
    contract.balanceOf(walletAddress).call(),
  ]);

  const dec = Number(decimals);
  const amountRaw = String(toSun(amountHuman, dec));

  if (BigInt(amountRaw) > BigInt(balance)) {
    outputJSON({ error: `Insufficient balance. Have ${fromSun(balance, dec)} ${symbol}, need ${amountHuman}` });
    process.exit(1);
  }

  const result = {
    action: "transfer",
    token: tokenAddress,
    symbol: String(symbol),
    from: walletAddress,
    to: toAddress,
    amount: amountHuman,
    amount_raw: amountRaw,
    dry_run: dryRun,
  };

  log(`Transfer ${amountHuman} ${symbol} to ${toAddress}`);

  if (dryRun) {
    result.status = "dry_run";
    log("Dry run — no transaction sent.");
    outputJSON(result);
    return;
  }

  try {
    const tx = await contract.transfer(toAddress, amountRaw).send({ feeLimit: 50_000_000, shouldPollResponse: false });
    result.status = "submitted";
    result.tx_id = tx;
    log(`Transaction submitted: ${tx}`);
  } catch (e) {
    result.status = "failed";
    result.error = e.message || String(e);
  }

  outputJSON(result);
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
