---
name: bankofai-guide
description: "Onboarding guide for BofAI skills — handles post-install setup, AgentWallet creation, and wallet guard when no wallet is configured."
version: 1.0.0
tags:
  - bankofai
  - onboarding
  - wallet
  - setup
  - guide
---

# BankOfAI Guide Skill

This skill handles three onboarding flows. Jump directly to the relevant section based on context.

---

## Section A — Post-Install Onboarding (Flow 1)

**Trigger:** User message mentions `bankofai-guide` onboarding, post-install setup, or equivalent request after running `npx skills add BofAI/skills`.

**Steps:**

1. Announce that skills installation is complete.
2. Run `npm install -g @bankofai/agent-wallet` to install the Agent Wallet CLI.
3. Run `agent-wallet list` silently to check wallet state.
4. Inform the user that a wallet is needed for transfers and trading, and ask whether they want to set one up now or later.
5. **User confirms** → proceed to **Section B**.
6. **User skips** → acknowledge and end.

---

## Section B — Wallet Creation / Display (Flow 2)

**Trigger:** User requests to create an AgentWallet, jumped from Section A, or jumped from Section C.

**Steps:**

1. Run `agent-wallet list`.

### If wallets already exist

1. Run `agent-wallet resolve-address` (omit wallet-id to use active wallet) to get EVM + TRON addresses.
2. Display both addresses clearly.
3. Ask the user whether they already have balance or need to deposit first:
   - **No balance / unsure** → guide the user to deposit USDT (TRC20) to the displayed address, and let them know they can come back for transfers or swaps after depositing.
   - **Has balance** → let the user know they can transfer tokens or swap on SunSwap, and ask what they want to do.

### If no wallets exist

Present two options:
- **Quick setup** (strongly recommended): fully automated, takes about 10 seconds
- **Detailed setup**: step-by-step configuration (wallet type selection, custom password, etc.)

#### Quick setup path

1. Locate the `agent-wallet` skill directory (the folder containing the `agent-wallet` SKILL.md), then run `node <agent-wallet-skill-dir>/scripts/generate-password.js` and capture the output as `<generated-password>`.
2. Run:
   ```bash
   agent-wallet start local_secure --override --save-runtime-secrets -g -w default_local_secure -p '<generated-password>'
   ```
3. Run `agent-wallet resolve-address default_local_secure -p '<generated-password>'` to get the addresses.
4. Display EVM and TRON addresses clearly. Note that the EVM address works across all EVM-compatible chains (Ethereum, BSC, Base, Polygon, Arbitrum, etc.).
5. Show the generated password to the user. Explain that this password encrypts the wallet's private key stored locally — it is required to sign transactions, resolve addresses, or perform any wallet operation. Inform them that the password has been auto-saved to `~/.agent-wallet/runtime_secrets.json` for convenience, but they should also memorize or securely store the password — if runtime secrets are deleted, the password is the only way to restore access to the wallet.
6. Guide the user to deposit USDT (TRC20) to the displayed address, and let them know they can come back for transfers or swaps after depositing.

#### Detailed setup path

Hand off to the `agent-wallet` skill and follow its full 4-step workflow (list → choose wallet type → collect options → execute).

---

## Section C — Wallet Guard (Flow 3)

**Purpose:** Called by other signing skills before any on-chain operation. Do not trigger this section for read-only queries.

**Steps:**

1. Run `agent-wallet list`.
2. **Wallets exist** → return control to the calling skill and continue the original operation.
3. **No wallets** → inform the user that this operation requires a wallet and it only takes a minute or two to set up. Ask if they want to create one now.
4. **User confirms** → proceed to **Section B**.
5. **User declines** → acknowledge and stop the original operation.
