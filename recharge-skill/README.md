# Recharge Skill

BANK OF AI account query and recharge skill.

## Quick Start

Read [SKILL.md](SKILL.md) for the full workflow, then use the local scripts or the remote MCP recharge endpoint depending on the task.

## What It Covers

- Query BANK OF AI point balances
- Query BANK OF AI order history
- Trigger remote recharge through `https://recharge.bankofai.io/mcp`
- Handle requests such as `recharge 1 usdt` or `给 BANK OF AI 充值 1 USDT`

## Files

- [SKILL.md](SKILL.md) - Full skill instructions and request routing rules
- [scripts/check_balance.js](scripts/check_balance.js) - Local balance lookup
- [scripts/check_orders.js](scripts/check_orders.js) - Local order lookup
- [scripts/lib/bankofai_config.js](scripts/lib/bankofai_config.js) - Config resolution helpers
- [bankofai-config.example.json](bankofai-config.example.json) - Example local config

## Local Configuration

Resolution order:

1. CLI arguments
2. Environment variables
3. `bankofai-config.json`
4. `~/.bankofai/config.json`
5. `~/.mcporter/bankofai-config.json`

## Usage Examples

```bash
node scripts/check_balance.js --format json
node scripts/check_orders.js --format json
```

For recharge requests, call the remote MCP tool:

```text
recharge(amount="1", token="USDT")
```

## Notes

- The skill must not store or print the user's BANK OF AI API key.
- Recharge uses the remote MCP endpoint; local scripts are only for balance and order queries.
- Recharge requests are sent over HTTPS to `https://recharge.bankofai.io/mcp`. Users should verify that endpoint before configuring credentials, because the BANK OF AI API key is transmitted to that service for recharge operations.

## License

MIT
