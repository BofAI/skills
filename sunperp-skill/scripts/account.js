#!/usr/bin/env node
/**
 * SunPerp Account Script
 *
 * Commands:
 *   balance                          -- Get account balance
 *   fee     [contract_code=BTC-USDT] -- Get trading fee rates
 *   bills   mar_acct=USDT [contract=BTC-USDT] [start_time=...] [end_time=...]
 */
import { privateGet, privatePost, printJson, exitWithError, parseArgs } from "./utils.js";

const command = process.argv[2];
const subArgv = ["", "", ...process.argv.slice(3)];

async function main() {
  switch (command) {
    case "balance": {
      const data = await privateGet("/sapi/v1/account/balance");
      printJson(data);
      break;
    }

    case "fee": {
      const args = parseArgs(subArgv, [], ["contract_code", "pair", "contract_type", "business_type"]);
      const data = await privatePost("/sapi/v1/account/fee_rate", {}, {
        contract_code: args.contract_code,
        pair: args.pair,
        contract_type: args.contract_type,
        business_type: args.business_type,
      });
      printJson(data);
      break;
    }

    case "bills": {
      const args = parseArgs(subArgv, ["mar_acct"], ["contract", "start_time", "end_time", "direct", "from_id"]);
      const data = await privatePost("/sapi/v1/account/bill_record", {}, {
        mar_acct: args.mar_acct,
        contract: args.contract,
        start_time: args.start_time,
        end_time: args.end_time,
        direct: args.direct,
        from_id: args.from_id,
      });
      printJson(data);
      break;
    }

    default:
      exitWithError(
        `Unknown command: ${command}\n` +
        "Available commands: balance, fee, bills"
      );
  }
}

main().catch((err) => exitWithError(err.message));
