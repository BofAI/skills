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

**Trigger:** User message contains the install phrase `bankofai-guide 進行配置引導` or equivalent post-install onboarding request.

**Steps:**

1. Announce: "技能安装完成！"
2. Run `agent-wallet --version` to check if the CLI is installed.
   - **Not installed** → say:
     > "要使用钱包功能，需要先安装 Agent Wallet CLI。要我帮你安装吗？"
   - **User confirms** → ask: "安装 stable 版本还是 beta 版本？"
     - **stable** → run `npm install -g @bankofai/agent-wallet`
     - **beta** → run `npm install -g @bankofai/agent-wallet@beta`
   - **User declines** → reply "没问题！需要的时候随时找我" and end.
3. Run `agent-wallet list` silently to check wallet state.
4. Say:
   > "如果你以后需要转账或交易，还需要配置一个钱包。现在就配还是以后再说？"
5. **User confirms** → proceed to **Section B**.
6. **User skips** → reply "没问题！需要的时候随时找我" and end.

---

## Section B — Wallet Creation / Display (Flow 2)

**Trigger:** User says "创建 AgentWallet 钱包", jumped from Section A, or jumped from Section C.

**Steps:**

1. Run `agent-wallet list`.

### If wallets already exist

1. Run `agent-wallet resolve-address` (omit wallet-id to use active wallet) to get EVM + TRON addresses.
2. Display both addresses clearly.
3. Ask: "你的钱包有余额了吗，还是需要先充值？"
   - **No balance / unsure** → say:
     > "你可以向这个地址充值 USDT（TRC20）开始使用。充值完成后告诉我，我帮你转账或兑换。"
   - **Has balance** → say:
     > "太好了！你现在可以转账或在 SunSwap 上兑换代币。告诉我你想做什么。"

### If no wallets exist

Ask:
> "还没有钱包。你想怎么建立？
> - **快速建立**：我帮你自动完成，30秒搞定
> - **详细设置**：一步步配置（选择钱包类型、自定义密码等）"

#### Quick setup path

1. Run `node agent-wallet/scripts/generate-password.js` and capture the output as `<generated-password>`.
2. Run:
   ```bash
   agent-wallet start local_secure --override --save-runtime-secrets -g -w default_local_secure -p '<generated-password>'
   ```
3. Run `agent-wallet resolve-address default_local_secure -p '<generated-password>'` to get the addresses.
4. Display EVM + TRON addresses clearly.
5. Display the password with this message:
   > "钱包已创建！密码已自动保存到 `~/.agent-wallet/runtime_secrets.json`，但请你也记住这个密码：`<generated-password>`。如果 runtime secrets 被删除，你需要用密码恢复访问。"
6. Say:
   > "你可以向上面的地址充值 USDT（TRC20）开始使用。充值完成后告诉我，我帮你转账或兑换。"

#### Detailed setup path

Hand off to the `agent-wallet` skill and follow its full 4-step workflow (list → choose wallet type → collect options → execute).

---

## Section C — Wallet Guard (Flow 3)

**Purpose:** Called by other signing skills before any on-chain operation. Do not trigger this section for read-only queries.

**Steps:**

1. Run `agent-wallet list`.
2. **Wallets exist** → return control to the calling skill and continue the original operation.
3. **No wallets** → say:
   > "这个操作需要用到钱包，但你还没创建。只需要一两分钟就能搞定，现在开始创建吗？"
4. **User confirms** → proceed to **Section B**.
5. **User declines** → reply "没问题，需要的时候随时找我" and stop the original operation.
