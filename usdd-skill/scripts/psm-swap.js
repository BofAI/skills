#!/usr/bin/env node

/**
 * psm-swap.js — Buy or sell USDT via the USDD Peg Stability Module.
 *
 * sell: Deposit USDT to PSM, receive USDD 1:1 (zero fee).
 * buy:  Deposit USDD to PSM, receive USDT 1:1 (zero fee).
 *
 * The amount is always in USDT terms (e.g., "1000" = 1000 USDT).
 * The script auto-handles TRC20 approval.
 *
 * Usage:
 *   node psm-swap.js <buy|sell> <amount> [--dry-run]
 *
 * Examples:
 *   node psm-swap.js sell 1000 --dry-run     # Preview: sell 1000 USDT -> receive 1000 USDD
 *   node psm-swap.js sell 500                 # Execute: sell 500 USDT for USDD
 *   node psm-swap.js buy 1000 --dry-run      # Preview: spend USDD -> receive 1000 USDT
 *   node psm-swap.js buy 250                  # Execute: buy 250 USDT with USDD
 */

const { CONTRACTS, getTronWeb, getNetwork, getContracts, resolveToken, toSun, fromSun, outputJSON, log } = require("./utils");

const MAX_UINT256 = "115792089237316195423570985008687907853269984665640564039457584007913129639935";

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error("Usage: node psm-swap.js <buy|sell> <amount> [--dry-run]");
    process.exit(1);
  }

  const direction = args[0].toLowerCase();
  if (direction !== "buy" && direction !== "sell") {
    console.error(`Invalid direction "${args[0]}". Use "buy" or "sell".`);
    process.exit(1);
  }

  const amountHuman = args[1];
  const dryRun = args.includes("--dry-run");

  const tronWeb = getTronWeb();
  const network = getNetwork();
  const contracts = getContracts();
  const walletAddress = tronWeb.defaultAddress.base58;

  const psmAddress = contracts.psm.address;
  const gemJoinAddress = contracts.psmGemJoin.address;
  const usdtToken = resolveToken("USDT");
  const usddToken = resolveToken("USDD");

  // gemAmt is always in USDT decimals (6)
  const gemAmtRaw = toSun(amountHuman, usdtToken.decimals);

  const result = {
    action: `psm_${direction}`,
    direction,
    amount_usdt: amountHuman,
    psm_address: psmAddress,
    wallet: walletAddress,
    dry_run: dryRun,
  };

  if (direction === "sell") {
    // sell USDT -> receive USDD
    result.input_token = "USDT";
    result.output_token = "USDD";
    log(`PSM sell: ${amountHuman} USDT -> USDD ...`);

    // Check USDT balance
    log("Checking USDT balance ...");
    const usdtContract = await tronWeb.contract(
      [CONTRACTS.abi.trc20.balanceOf],
      usdtToken.address
    );
    const usdtBalance = BigInt(await usdtContract.balanceOf(walletAddress).call());
    result.usdt_balance = fromSun(usdtBalance, usdtToken.decimals);

    if (usdtBalance < gemAmtRaw) {
      result.status = "failed";
      result.error = `Insufficient USDT balance. Have: ${result.usdt_balance}, Need: ${amountHuman}`;
      outputJSON(result);
      return;
    }

    // Check USDT approval to PSM GemJoin
    log("Checking USDT allowance for PSM GemJoin ...");
    const approvalContract = await tronWeb.contract(
      [CONTRACTS.abi.trc20.allowance, CONTRACTS.abi.trc20.approve],
      usdtToken.address
    );
    const allowance = BigInt(await approvalContract.allowance(walletAddress, gemJoinAddress).call());
    result.current_allowance = fromSun(allowance, usdtToken.decimals);
    result.needs_approval = allowance < gemAmtRaw;

    if (dryRun) {
      result.status = "dry_run";
      log("Dry run complete.");
      outputJSON(result);
      return;
    }

    // Approve if needed
    if (allowance < gemAmtRaw) {
      log("Approving PSM GemJoin to spend USDT ...");
      const approveTx = await approvalContract.approve(gemJoinAddress, MAX_UINT256).send({
        feeLimit: 50_000_000,
        shouldPollResponse: false,
      });
      result.approve_tx = approveTx;
      log(`Approval tx: ${approveTx}`);
      await new Promise((r) => setTimeout(r, 4000));
    }

    // Execute sellGem
    log("Executing PSM sellGem ...");
    const psmContract = await tronWeb.contract(
      [CONTRACTS.abi.psm.sellGem],
      psmAddress
    );
    const tx = await psmContract.sellGem(walletAddress, String(gemAmtRaw)).send({
      feeLimit: 150_000_000,
      shouldPollResponse: false,
    });
    result.status = "submitted";
    result.tx_id = tx;
    result.expected_usdd = amountHuman;
    log(`Transaction: ${tx}`);

  } else {
    // buy USDT <- spend USDD
    result.input_token = "USDD";
    result.output_token = "USDT";
    log(`PSM buy: spend USDD -> ${amountHuman} USDT ...`);

    // Calculate USDD needed (1:1 but different decimals: USDD=18, USDT=6)
    const usddNeeded = toSun(amountHuman, usddToken.decimals);

    // Check USDD balance
    log("Checking USDD balance ...");
    const usddContract = await tronWeb.contract(
      [CONTRACTS.abi.trc20.balanceOf],
      usddToken.address
    );
    const usddBalance = BigInt(await usddContract.balanceOf(walletAddress).call());
    result.usdd_balance = fromSun(usddBalance, usddToken.decimals);

    if (usddBalance < usddNeeded) {
      result.status = "failed";
      result.error = `Insufficient USDD balance. Have: ${result.usdd_balance}, Need: ${amountHuman}`;
      outputJSON(result);
      return;
    }

    // buyGem does dai.transferFrom(msg.sender, address(this), ...) directly,
    // so approval must target the PSM contract itself.
    log("Checking USDD allowance for PSM ...");
    const approvalContract = await tronWeb.contract(
      [CONTRACTS.abi.trc20.allowance, CONTRACTS.abi.trc20.approve],
      usddToken.address
    );
    const allowance = BigInt(await approvalContract.allowance(walletAddress, psmAddress).call());
    result.current_allowance = fromSun(allowance, usddToken.decimals);
    result.needs_approval = allowance < usddNeeded;

    if (dryRun) {
      result.status = "dry_run";
      log("Dry run complete.");
      outputJSON(result);
      return;
    }

    // Approve if needed
    if (allowance < usddNeeded) {
      log("Approving PSM to spend USDD ...");
      const approveTx = await approvalContract.approve(psmAddress, MAX_UINT256).send({
        feeLimit: 50_000_000,
        shouldPollResponse: false,
      });
      result.approve_tx = approveTx;
      log(`Approval tx: ${approveTx}`);
      await new Promise((r) => setTimeout(r, 4000));
    }

    // Execute buyGem
    log("Executing PSM buyGem ...");
    const psmContract = await tronWeb.contract(
      [CONTRACTS.abi.psm.buyGem],
      psmAddress
    );
    const tx = await psmContract.buyGem(walletAddress, String(gemAmtRaw)).send({
      feeLimit: 150_000_000,
      shouldPollResponse: false,
    });
    result.status = "submitted";
    result.tx_id = tx;
    result.expected_usdt = amountHuman;
    log(`Transaction: ${tx}`);
  }

  outputJSON(result);
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
