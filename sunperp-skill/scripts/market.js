#!/usr/bin/env node
/**
 * SunPerp Market Data Script
 *
 * Commands:
 *   ticker   contract_code=BTC-USDT
 *   depth    contract_code=BTC-USDT [type=step0]
 *   kline    contract_code=BTC-USDT [period=1hour] [size=50]
 *   bbo      [contract_code=BTC-USDT]
 *   trade    [contract_code=BTC-USDT]
 *   trades   contract_code=BTC-USDT [size=20]
 *   funding  contract_code=BTC-USDT
 *   index    [contract_code=BTC-USDT]
 *   contracts [contract_code=BTC-USDT]
 *   price_limit [contract_code=BTC-USDT]
 */
import { publicGet, printJson, exitWithError, parseArgs } from "./utils.js";

const command = process.argv[2];
// Shift argv so parseArgs starts from index 3
const subArgv = ["", "", ...process.argv.slice(3)];

async function main() {
  switch (command) {
    case "ticker": {
      const args = parseArgs(subArgv, ["contract_code"]);
      const data = await publicGet("/sapi/v1/market/detail/merged", {
        contract_code: args.contract_code,
      });
      printJson(data);
      break;
    }

    case "depth": {
      const args = parseArgs(subArgv, ["contract_code"], ["type"]);
      const data = await publicGet("/sapi/v1/market/depth", {
        contract_code: args.contract_code,
        type: args.type || "step0",
      });
      printJson(data);
      break;
    }

    case "kline": {
      const args = parseArgs(subArgv, ["contract_code"], ["period", "size"]);
      const data = await publicGet("/sapi/v1/market/history/kline", {
        contract_code: args.contract_code,
        period: args.period || "60min",
        size: args.size || "50",
      });
      printJson(data);
      break;
    }

    case "bbo": {
      const args = parseArgs(subArgv, [], ["contract_code"]);
      const data = await publicGet("/sapi/v1/market/bbo", {
        contract_code: args.contract_code,
      });
      printJson(data);
      break;
    }

    case "trade": {
      const args = parseArgs(subArgv, [], ["contract_code"]);
      const data = await publicGet("/sapi/v1/market/trade", {
        contract_code: args.contract_code,
      });
      printJson(data);
      break;
    }

    case "trades": {
      const args = parseArgs(subArgv, ["contract_code"], ["size"]);
      const data = await publicGet("/sapi/v1/market/history/trade", {
        contract_code: args.contract_code,
        size: args.size || "20",
      });
      printJson(data);
      break;
    }

    case "funding": {
      const args = parseArgs(subArgv, ["contract_code"]);
      const data = await publicGet("/sapi/v1/public/funding_rate", {
        contract_code: args.contract_code,
      });
      printJson(data);
      break;
    }

    case "index": {
      const args = parseArgs(subArgv, [], ["contract_code"]);
      const data = await publicGet("/sapi/v1/public/index", {
        contract_code: args.contract_code,
      });
      printJson(data);
      break;
    }

    case "contracts": {
      const args = parseArgs(subArgv, [], ["contract_code"]);
      const data = await publicGet("/sapi/v1/public/contract_info", {
        contract_code: args.contract_code,
      });
      printJson(data);
      break;
    }

    case "price_limit": {
      const args = parseArgs(subArgv, [], ["contract_code"]);
      const data = await publicGet("/sapi/v1/public/price_limit", {
        contract_code: args.contract_code,
      });
      printJson(data);
      break;
    }

    default:
      exitWithError(
        `Unknown command: ${command}\n` +
        "Available commands: ticker, depth, kline, bbo, trade, trades, funding, index, contracts, price_limit"
      );
  }
}

main().catch((err) => exitWithError(err.message));
