#!/usr/bin/env node
/**
 * SunPerp Order Management Script
 *
 * Commands:
 *   place          -- Place a single order
 *   cancel         -- Cancel a single order
 *   cancel_all     -- Cancel all orders
 *   close          -- Close position for a symbol at market price
 *   close_all      -- Close all positions at market price
 *   open_orders    -- List open orders
 *   info           -- Get order info
 *   history        -- Get order history
 *   details        -- Get execution details
 *
 * Place order args:
 *   contract_code=BTC-USDT side=buy type=limit volume=1 [price=50000]
 *   [margin_mode=cross] [position_side=both] [reduce_only=0]
 *   [time_in_force=GTC] [tp_trigger_price=...] [sl_trigger_price=...]
 *   [client_order_id=...]
 */
import { privateGet, privatePost, printJson, exitWithError, parseArgs } from "./utils.js";

const command = process.argv[2];
const subArgv = ["", "", ...process.argv.slice(3)];

async function main() {
  switch (command) {
    case "place": {
      const args = parseArgs(
        subArgv,
        ["contract_code", "side", "type", "volume"],
        [
          "price", "margin_mode", "position_side", "reduce_only",
          "time_in_force", "client_order_id", "price_match",
          "tp_trigger_price", "tp_order_price", "tp_type", "tp_trigger_price_type",
          "sl_trigger_price", "sl_order_price", "sl_type", "sl_trigger_price_type",
          "price_protect", "self_match_prevent",
        ]
      );
      const body = {
        contract_code: args.contract_code,
        margin_mode: args.margin_mode || "cross",
        side: args.side,
        type: args.type,
        volume: Number(args.volume),
        price: args.price ? Number(args.price) : undefined,
        position_side: args.position_side,
        reduce_only: args.reduce_only !== undefined ? Number(args.reduce_only) : undefined,
        time_in_force: args.time_in_force,
        client_order_id: args.client_order_id,
        price_match: args.price_match,
        tp_trigger_price: args.tp_trigger_price ? Number(args.tp_trigger_price) : undefined,
        tp_order_price: args.tp_order_price ? Number(args.tp_order_price) : undefined,
        tp_type: args.tp_type,
        tp_trigger_price_type: args.tp_trigger_price_type,
        sl_trigger_price: args.sl_trigger_price ? Number(args.sl_trigger_price) : undefined,
        sl_order_price: args.sl_order_price ? Number(args.sl_order_price) : undefined,
        sl_type: args.sl_type,
        sl_trigger_price_type: args.sl_trigger_price_type,
        price_protect: args.price_protect,
        self_match_prevent: args.self_match_prevent,
      };
      const data = await privatePost("/sapi/v1/trade/order", {}, body);
      printJson(data);
      break;
    }

    case "cancel": {
      const args = parseArgs(subArgv, ["contract_code"], ["order_id", "client_order_id"]);
      if (!args.order_id && !args.client_order_id) {
        exitWithError("Either order_id or client_order_id is required");
      }
      const data = await privatePost("/sapi/v1/trade/cancel_order", {}, {
        contract_code: args.contract_code,
        order_id: args.order_id,
        client_order_id: args.client_order_id,
      });
      printJson(data);
      break;
    }

    case "cancel_all": {
      const args = parseArgs(subArgv, [], ["contract_code", "side", "position_side"]);
      const data = await privatePost("/sapi/v1/trade/cancel_all_orders", {}, {
        contract_code: args.contract_code,
        side: args.side,
        position_side: args.position_side,
      });
      printJson(data);
      break;
    }

    case "close": {
      const args = parseArgs(subArgv, ["contract_code", "position_side"], ["margin_mode", "client_order_id"]);
      const data = await privatePost("/sapi/v1/trade/position", {}, {
        contract_code: args.contract_code,
        margin_mode: args.margin_mode || "cross",
        position_side: args.position_side,
        client_order_id: args.client_order_id,
      });
      printJson(data);
      break;
    }

    case "close_all": {
      const data = await privatePost("/sapi/v1/trade/position_all", {}, {});
      printJson(data);
      break;
    }

    case "open_orders": {
      const args = parseArgs(subArgv, [], ["contract_code", "margin_mode", "limit", "direct"]);
      const data = await privateGet("/sapi/v1/trade/order/opens", {
        contract_code: args.contract_code,
        margin_mode: args.margin_mode,
        limit: args.limit,
        direct: args.direct,
      });
      printJson(data);
      break;
    }

    case "info": {
      const args = parseArgs(subArgv, ["contract_code"], ["order_id", "client_order_id", "margin_mode"]);
      if (!args.order_id && !args.client_order_id) {
        exitWithError("Either order_id or client_order_id is required");
      }
      const data = await privateGet("/sapi/v1/trade/order", {
        contract_code: args.contract_code,
        order_id: args.order_id,
        client_order_id: args.client_order_id,
        margin_mode: args.margin_mode,
      });
      printJson(data);
      break;
    }

    case "history": {
      const args = parseArgs(subArgv, ["contract_code"], ["margin_mode", "state", "type", "start_time", "end_time", "limit", "direct"]);
      const data = await privateGet("/sapi/v1/trade/order/history", {
        contract_code: args.contract_code,
        margin_mode: args.margin_mode || "cross",
        state: args.state,
        type: args.type,
        start_time: args.start_time,
        end_time: args.end_time,
        limit: args.limit,
        direct: args.direct,
      });
      printJson(data);
      break;
    }

    case "details": {
      const args = parseArgs(subArgv, [], ["contract_code", "order_id", "start_time", "end_time", "limit", "direct"]);
      const data = await privateGet("/sapi/v1/trade/order/details", {
        contract_code: args.contract_code,
        order_id: args.order_id,
        start_time: args.start_time,
        end_time: args.end_time,
        limit: args.limit,
        direct: args.direct,
      });
      printJson(data);
      break;
    }

    default:
      exitWithError(
        `Unknown command: ${command}\n` +
        "Available commands: place, cancel, cancel_all, close, close_all, open_orders, info, history, details"
      );
  }
}

main().catch((err) => exitWithError(err.message));
