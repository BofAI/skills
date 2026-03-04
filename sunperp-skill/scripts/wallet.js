#!/usr/bin/env node
/**
 * SunPerp Wallet Script
 *
 * Commands:
 *   withdraw  address=TXxx... amount=1 [currency=usdt] [chain=trc20usdt] [fee=0]
 *             Full withdraw flow: apply → sign with TRON key → confirm
 *             Requires TRON_PRIVATE_KEY env var for signing the confirm step.
 *
 *   apply     address=TXxx... amount=1 [currency=usdt] [chain=trc20usdt] [fee=0]
 *             Step 1 only: returns nonce + content for manual signing.
 *
 *   confirm   nonce=<nonce> signature=<hex_signature>
 *             Step 2 only: confirm a previously applied withdrawal.
 *
 *   records   type=deposit|withdraw [currency=usdt] [size=50] [direct=next] [from=<id>]
 *             Query deposit or withdrawal history.
 */
import { TronWeb } from "tronweb";
import { walletPost, walletGet, printJson, exitWithError, parseArgs } from "./utils.js";

const command = process.argv[2];
const subArgv = ["", "", ...process.argv.slice(3)];

function getTronPrivateKey() {
  const pk = process.env.TRON_PRIVATE_KEY;
  if (!pk) {
    exitWithError(
      "Missing TRON_PRIVATE_KEY environment variable.\n" +
      "Set it to sign withdrawal confirmations:\n" +
      '  export TRON_PRIVATE_KEY="your_hex_private_key"'
    );
  }
  return pk;
}

async function signContent(content) {
  const pk = getTronPrivateKey();
  const tronWeb = new TronWeb({ fullHost: "https://api.trongrid.io", privateKey: pk });
  const signed = await tronWeb.trx.signMessageV2(content);
  return signed;
}

async function main() {
  switch (command) {
    // ----- Full withdraw: apply → sign → confirm -----
    case "withdraw": {
      const args = parseArgs(subArgv, ["address", "amount"], ["currency", "chain", "fee"]);

      // Step 1: Apply
      console.log("Step 1/2: Submitting withdraw request...");
      const applyResult = await walletPost("/sapi/v1/sunperp/dw/withdraw/apply", {
        address: args.address,
        currency: args.currency || "usdt",
        chain: args.chain || "trc20usdt",
        amount: args.amount,
        fee: args.fee || "0",
      });

      if (applyResult.status === "error" || applyResult["error-code"]) {
        exitWithError(
          `Withdraw apply failed: ${applyResult["error-msg"] || applyResult.message || JSON.stringify(applyResult)}`
        );
      }

      const { nonce, content } = applyResult.data;
      const expiresAt = applyResult.data["expired-at"];
      console.log(`  Nonce: ${nonce}`);
      console.log(`  Expires: ${new Date(expiresAt).toISOString()} (120s window)`);
      console.log(`  Content to sign: ${content}`);

      // Step 2: Sign + Confirm
      console.log("\nStep 2/2: Signing and confirming...");
      const signature = await signContent(content);
      console.log(`  Signature: ${signature}`);

      const confirmResult = await walletPost("/sapi/v1/sunperp/dw/withdraw/confirm", {
        nonce,
        signature,
      });

      if (confirmResult.status === "error" || confirmResult["error-code"]) {
        exitWithError(
          `Withdraw confirm failed: ${confirmResult["error-msg"] || confirmResult.message || JSON.stringify(confirmResult)}`
        );
      }

      console.log("\nWithdrawal submitted successfully:");
      printJson(confirmResult);
      break;
    }

    // ----- Apply only (step 1) -----
    case "apply": {
      const args = parseArgs(subArgv, ["address", "amount"], ["currency", "chain", "fee"]);
      const data = await walletPost("/sapi/v1/sunperp/dw/withdraw/apply", {
        address: args.address,
        currency: args.currency || "usdt",
        chain: args.chain || "trc20usdt",
        amount: args.amount,
        fee: args.fee || "0",
      });
      printJson(data);
      break;
    }

    // ----- Confirm only (step 2) -----
    case "confirm": {
      const args = parseArgs(subArgv, ["nonce", "signature"]);
      const data = await walletPost("/sapi/v1/sunperp/dw/withdraw/confirm", {
        nonce: args.nonce,
        signature: args.signature,
      });
      printJson(data);
      break;
    }

    // ----- Deposit/Withdraw records -----
    case "records": {
      const args = parseArgs(subArgv, ["type"], ["currency", "size", "direct", "from"]);
      const data = await walletGet("/sapi/v1/sunperp/dw/query/deposit-withdraw", {
        type: args.type,
        currency: args.currency,
        size: args.size,
        direct: args.direct,
        from: args.from,
      });
      printJson(data);
      break;
    }

    default:
      exitWithError(
        `Unknown command: ${command}\n` +
        "Available commands: withdraw, apply, confirm, records"
      );
  }
}

main().catch((err) => exitWithError(err.message));
