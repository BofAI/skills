---
name: ainft-skill
description: "AINFT 本地技能：管理用户 API Key，查询余额/额度，并调用 AINFT Merchant Agent 支付工具。"
version: 1.0.0
tags:
  - ainft
  - balance
  - quota
  - recharge
  - mcp
---

# AINFT Local Skill

目标：
- 在用户本地 Agent 管理和使用用户自己的 `AINFT_API_KEY`
- 执行余额查询、额度查询（不经过 ainft server）
- 在需要充值时调用 `ainft-merchant-agent` 的独立 MCP 支付工具
  - `ainft_pay_trc20`（x402）
  - `ainft_pay_trx`（TRX 原生转账）

## 安全边界

- 不把用户 `AINFT_API_KEY` 发给 `ainft server`
- `AINFT_API_KEY` 仅在本地 Agent 环境变量或本地配置中使用
- `ainft server` 只处理充值，不处理用户余额/额度查询

## 本地配置

推荐将 `AINFT_API_KEY` 放在本地配置文件，环境变量作为覆盖项：

- `ainft-config.json`（当前目录）或 `~/.ainft/config.json` 或 `~/.mcporter/ainft-config.json`
- 示例见：`ainft-config.example.json`

```json
{
  "api_key": "ak-xxxx",
  "base_url": "https://chat-dev.ainft.com",
  "timeout_ms": 15000
}
```

也支持环境变量：

- `AINFT_API_KEY=<user api key>`
- `AINFT_BASE_URL=https://chat-dev.ainft.com`（可切 prod）
- `AINFT_TIMEOUT_MS=15000`（可选）
- `AINFT_MCP_URL=<merchant-agent mcp endpoint>`（例如 `https://tn-ainft.bankofai.io/mcp`）
- `TRON_PRIVATE_KEY=<local wallet key>`（TRX 原生转账必需）
- `AINFT_TRON_RPC_URL=https://nile.trongrid.io`（TRX 原生转账 RPC，可选）

AINFT 查询脚本配置优先级（`check_balance.js` / `check_quota.js`）：
1. 命令行参数（`--api-key`、`--base-url`、`--timeout-ms`）
2. 环境变量（`AINFT_API_KEY`、`AINFT_BASE_URL`、`AINFT_TIMEOUT_MS`）
3. 本地配置文件（`ainft-config.json` / `~/.ainft/config.json` / `~/.mcporter/ainft-config.json`）
4. 默认值（`https://chat-dev.ainft.com`、`15000ms`）

TRON 私钥读取优先级（`pay_trx_native.js`）：
1. `--private-key`
2. 环境变量：`TRON_PRIVATE_KEY` / `PRIVATE_KEY`
3. `x402-config.json`（当前目录）
4. `~/.x402-config.json`
5. `~/.mcporter/mcporter.json`（`mcpServers.*.env.TRON_PRIVATE_KEY`）

## 可用脚本

- 余额查询：
  - `node scripts/check_balance.js --format text`
- 额度查询（默认调用 `usage.points`）：
  - `node scripts/check_quota.js --format text`
  - 可指定 procedure：`--procedure usage.points`
- 本地阈值判断（可选）：
  - `node scripts/quota_guard.js --requested 20000`
- TRX 原生充值闭环（自动“转账 + 回调校验”）：
  - `node scripts/pay_trx_native.js --amount 1 --mcp-url "$AINFT_MCP_URL"`

## 充值调用规范（MCP）

1. TRC20 充值（x402）：
   - MCP tool: `ainft_pay_trc20`
   - 参数示例：`{"amount":"1","token":"USDT"}`
2. TRX 充值（原生，不走 x402）：
   - MCP tool: `ainft_pay_trx`
   - 可直接使用脚本自动闭环：`scripts/pay_trx_native.js`
   - 或手动两段式：
     - 第一次调用获取转账指令：`{"amount":"1"}`
     - 转账后带 `txid` 再次调用：`{"amount":"1","txid":"<tx_hash>"}`

## 执行顺序建议

1. 先跑 `check_balance.js` 和 `check_quota.js`
2. 若需充值，按资产类型选择 MCP 工具：
   - TRC20 -> `ainft_pay_trc20`
   - TRX -> `ainft_pay_trx`
3. 充值完成后再次查询余额/额度，向用户回报结果
