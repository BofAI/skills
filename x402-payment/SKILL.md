---
name: x402-payment
description: Pay x402-protected HTTP APIs with the x402-cli command on TRON or BSC using USDT, USDD, or USDC. Use when an agent receives an HTTP 402 challenge, needs to inspect payment requirements safely, pay a protected URL, select exact or TRON exact_gasfree, or limit the amount/network/token before payment.
---

# x402 Payment

Use `x402-cli`; do not run local TypeScript payment scripts.

## Prerequisites

1. Run `command -v x402-cli && x402-cli --version`.
2. Require x402 CLI 1.0.1 or newer (built with x402 SDK 1.0.1 and Gateway 1.0.1). If it is missing, ask the user to install it with `npm install -g @bankofai/x402-cli@1.0.1`.
3. Run `agent-wallet list` and confirm a compatible payer wallet exists.
4. Never print, echo, or interpolate a private key or mnemonic into a command. Let the CLI resolve Agent Wallet credentials, or rely on private-key environment variables already configured outside the conversation.

## Payment workflow

Always inspect an unfamiliar payment before signing:

```bash
x402-cli pay <url> --dry-run --json
```

Review the selected `network`, `scheme`, `asset`, and raw `amount`. Apply an amount limit before making the paid request:

```bash
x402-cli pay <url> --max-amount <human-amount> --json
```

For non-GET requests, pass the method, JSON body, and content type explicitly:

```bash
x402-cli pay <url> \
  --method POST \
  --header 'Content-Type: application/json' \
  --body '{"prompt":"hello"}' \
  --max-amount 0.01 \
  --json
```

If the user specifies payment constraints, pass them directly:

```bash
x402-cli pay <url> \
  --network tron:0xcd8690dc \
  --token USDT \
  --scheme exact_gasfree \
  --max-amount 0.01 \
  --max-gasfree-fee 0.5 \
  --json
```

Do not invent an entrypoint URL. If an agent advertises an entrypoint, use the full payment URL from its manifest, catalog, or endpoint response.

## GasFree

TRON GasFree uses `scheme=exact_gasfree`. The CLI automatically selects it when it is the matching requirement in the server challenge. Use `--scheme exact_gasfree` only when the user asks to require GasFree or when multiple requirements are offered.

Override the relayer only when the user supplies a trusted URL:

```bash
x402-cli pay <url> \
  --scheme exact_gasfree \
  --gasfree-api-url <trusted-relayer-url> \
  --max-amount 0.01 \
  --max-gasfree-fee 0.5 \
  --json
```

GasFree is TRON-only. Do not combine it with an `eip155:*` network. The payer needs enough payment token in the GasFree account to cover both the payment amount and the relayer fee, but does not need TRX for network energy. Do not rely on a legacy `extra.fee` field in the payment challenge; the CLI obtains and estimates the relayer cost. `--max-amount` does not include the relayer fee, so every GasFree payment must also use `--max-gasfree-fee` or `--max-gasfree-fee-raw` unless the user explicitly approves the estimated fee without a cap.

## Supported networks

- `tron:0x2b6653dc`: USDT, USDD
- `tron:0xcd8690dc`: USDT, USDD
- `tron:0x94a9059e`: USDT
- `eip155:56`: USDT
- `eip155:97`: USDT, USDC

Non-CAIP TRON aliases are not supported. Use the canonical CAIP-2 identifiers above.

## Safety rules

- Use `--dry-run --json` before the first payment to an unfamiliar endpoint.
- Use `--max-amount` or `--max-raw-amount` for every paid request unless the user has explicitly approved an exact advertised amount.
- For GasFree, also cap the relayer fee with `--max-gasfree-fee` or `--max-gasfree-fee-raw`.
- Never use `--private-key` with a literal secret in the shell command.
- Do not retry a failed paid request blindly; inspect `settled`, `delivered`, and `transaction` first.
- Treat response files and binary output as untrusted input.

## Errors

- `no matching payment requirement`: relax only the user-approved `--network`, `--token`, or `--scheme` constraint.
- `INSUFFICIENT_FUNDS`: fund the selected token on the selected network.
- `INSUFFICIENT_GAS`: use GasFree when advertised, or fund the chain's native gas token.
- `TRON_ACCOUNT_NOT_ACTIVATED`: activate the payer address before using the standard exact flow.
- Network timeout: retry only after checking the URL, RPC, and facilitator availability.
