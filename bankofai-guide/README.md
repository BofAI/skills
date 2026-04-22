# BankOfAI Guide Skill

Onboarding and wallet-guard guide for BANK OF AI skills.

## Quick Start

Use this guide after skill installation, when a user needs their first Agent Wallet, or when another signing skill needs to stop and require wallet setup.

## What It Covers

- Post-install onboarding after `npx skills add https://github.com/BofAI/skills.git`
- Quick wallet bootstrap through `agent-wallet`
- Wallet guard flow when a signing skill detects no wallet is configured

## Files

- [SKILL.md](SKILL.md) - Full onboarding flow, wallet-guard rules, and quick setup steps

## Main Flows

- Section A: post-install onboarding
- Section B: wallet creation or wallet display
- Section C: wallet guard for signing skills

## Notes

- This guide delegates wallet operations to the `agent-wallet` skill.
- It is intended to be used as orchestration and onboarding context, not as a signing implementation itself.

## License

MIT
