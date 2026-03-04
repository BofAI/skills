#!/usr/bin/env node
/**
 * SunPerp Position Management Script
 *
 * Commands:
 *   list             [contract_code=BTC-USDT]     -- List open positions
 *   get_leverage     [contract_code=BTC-USDT]     -- Get current leverage
 *   set_leverage     contract_code=BTC-USDT lever_rate=10  -- Set leverage
 *   get_mode                                       -- Get position mode (single_side/dual_side)
 *   set_mode         position_mode=single_side     -- Set position mode
 *   risk_limit       [contract_code=BTC-USDT]     -- Get risk limits
 *   position_limit   [contract_code=BTC-USDT]     -- Get position limits
 */
import { privateGet, privatePost, printJson, exitWithError, parseArgs } from "./utils.js";

const command = process.argv[2];
const subArgv = ["", "", ...process.argv.slice(3)];

async function main() {
  switch (command) {
    case "list": {
      const args = parseArgs(subArgv, [], ["contract_code"]);
      const data = await privateGet("/sapi/v1/trade/position/opens", {
        contract_code: args.contract_code,
      });
      printJson(data);
      break;
    }

    case "get_leverage": {
      const args = parseArgs(subArgv, [], ["contract_code", "margin_mode"]);
      const data = await privateGet("/sapi/v1/position/lever", {
        contract_code: args.contract_code,
        margin_mode: args.margin_mode,
      });
      printJson(data);
      break;
    }

    case "set_leverage": {
      const args = parseArgs(subArgv, ["contract_code", "lever_rate"], ["margin_mode"]);
      const data = await privatePost("/sapi/v1/position/lever", {}, {
        contract_code: args.contract_code,
        margin_mode: args.margin_mode || "cross",
        lever_rate: Number(args.lever_rate),
      });
      printJson(data);
      break;
    }

    case "get_mode": {
      const args = parseArgs(subArgv, [], ["margin_mode"]);
      const data = await privateGet("/sapi/v1/position/mode", {
        margin_mode: args.margin_mode,
      });
      printJson(data);
      break;
    }

    case "set_mode": {
      const args = parseArgs(subArgv, ["position_mode"]);
      const data = await privatePost("/sapi/v1/position/mode", {}, {
        position_mode: args.position_mode,
      });
      printJson(data);
      break;
    }

    case "risk_limit": {
      const args = parseArgs(subArgv, [], ["contract_code", "margin_mode", "position_side"]);
      const data = await privateGet("/sapi/v1/position/risk/limit", {
        contract_code: args.contract_code,
        margin_mode: args.margin_mode,
        position_side: args.position_side,
      });
      printJson(data);
      break;
    }

    case "position_limit": {
      const args = parseArgs(subArgv, [], ["contract_code", "pair", "contract_type", "business_type"]);
      const data = await privatePost("/sapi/v1/position/position_limit", {}, {
        contract_code: args.contract_code,
        pair: args.pair,
        contract_type: args.contract_type,
        business_type: args.business_type,
      });
      printJson(data);
      break;
    }

    default:
      exitWithError(
        `Unknown command: ${command}\n` +
        "Available commands: list, get_leverage, set_leverage, get_mode, set_mode, risk_limit, position_limit"
      );
  }
}

main().catch((err) => exitWithError(err.message));
