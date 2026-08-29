# Changelog

## Unreleased

- Add read-only security checks for accounts, tokens, URLs, transactions, multi-signature
  permissions, and token approvals
- Validate TRON addresses, transaction hashes, token identifiers, and URLs before querying APIs
  that otherwise return silent default or partial results for malformed input
- Add normalized assessment signals while preserving the complete TronScan response
- Report incomplete upstream security responses as `unknown` instead of a clean result
- Add offline tests plus live endpoint smoke-test coverage
- Require token identifiers for TRC10/TRC20 address-history queries, matching the current API

## 1.0.0 (2026-02-28)

- Initial release
- 8 lookup scripts: search, account, transaction, token, block, contract, transfer, overview
- Common token address registry (mainnet + nile testnet)
- API configuration with all 40+ TronScan endpoints
- Shared utility module with API client, argument parsing, and formatters
