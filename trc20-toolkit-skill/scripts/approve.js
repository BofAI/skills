#!/usr/bin/env node

/**
 * approve.js — Approve TRC20 token allowance or check existing allowance.
 *
 * Usage:
 *   node approve.js <token> <spender> <amount|max> [--dry-run]
 *   node approve.js <token> <spender> --check [walletAddress]
 *
 * Environment:
 *   TRON_PRIVATE_KEY, TRON_NETWORK (mainnet|nile), TRONGRID_API_KEY (optional)
 */

const { TRC20_ABI, MAX_UINT256, getTronWeb, resolveToken, toSun, fromSun, outputJSON, log } = require("./utils");

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 3) { console.error("Usage: node approve.js <token> <spender> <amount|max|--check> [--dry-run]"); process.exit(1); }

  const tronWeb = getTronWeb();
  const tokenAddress = resolveToken(args[0]);
  const spenderAddress = args[1];
  const isCheck = args[2] === "--check";

  const contract = await tronWeb.contract(TRC20_ABI, tokenAddress);
  const [decimals, symbol] = await Promise.all([
    contract.decimals().call(),
    contract.symbol().call(),
  ]);
  const dec = Number(decimals);

  if (isCheck) {
    const owner = args[3] || tronWeb.defaultAddress.base58;
    const allowance = await contract.allowance(owner, spenderAddress).call();
    outputJSON({
      action: "check_allowance",
      token: tokenAddress,
      symbol: String(symbol),
      owner,
      spender: spenderAddress,
      allowance: fromSun(allowance, dec),
      allowance_raw: String(allowance),
      is_max: String(allowance) === MAX_UINT256,
    });
    return;
  }

  const amountArg = args[2];
  const dryRun = args.includes("--dry-run");
  const amountRaw = amountArg.toLowerCase() === "max" ? MAX_UINT256 : String(toSun(amountArg, dec));

  const result = {
    action: "approve",
    token: tokenAddress,
    symbol: String(symbol),
    spender: spenderAddress,
    amount: amountArg.toLowerCase() === "max" ? "unlimited" : amountArg,
    amount_raw: amountRaw,
    dry_run: dryRun,
  };

  log(`Approve ${result.amount} ${symbol} for ${spenderAddress}`);

  if (dryRun) {
    result.status = "dry_run";
    outputJSON(result);
    return;
  }

  try {
    const tx = await contract.approve(spenderAddress, amountRaw).send({ feeLimit: 50_000_000, shouldPollResponse: false });
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
