<h1 align="center">BANK OF AI Skills</h1>

<p align="center">
  <a href="https://github.com/BofAI/skills">
    <img src="https://img.shields.io/badge/GitHub-BofAI%2Fskills-blue" alt="GitHub" />
  </a>
  <a href="./LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT" />
  </a>
</p>

A curated collection of practical, DeFi-focused utility skills developed by the **BANK OF AI team**. These skills enable AI agents to perform complex on-chain operations, payments, and identity management across various platforms.

> **Project Positioning:** We focus on delivering high-value DeFi utility skills that are platform-agnostic. These skills provide the domain knowledge needed to interact with the TRON blockchain and beyond.

---

## Contents

- [What are BANK OF AI Skills?](#what-are-bank-of-ai-skills)
- [Installation](#installation)
- [Available Skills](#available-skills)
  - [DeFi & DEX](#defi--dex)
  - [Payments & x402](#payments--x402)
  - [AI & Account Recharge](#ai--account-recharge)
  - [Data & Analytics](#data--analytics)
- [Usage Tips](#usage-tips)
  - [Explicit Invocation](#explicit-invocation)
  - [Implicit Triggering](#implicit-triggering)
- [Creating Skills](#creating-skills)
- [Contributing](#contributing)
- [License](#license)

---

## What are BANK OF AI Skills?

BANK OF AI Skills are reusable, task-oriented capabilities that teach AI agents how to perform specific blockchain workflows. Each skill encapsulates domain knowledge (like SunSwap pathfinding) and provides step-by-step instructions for the agent to follow.

## Installation

Use the unified installer and follow the `npx` prompts to select the skills you want and the agentic platform you use. The installer will complete the setup automatically.

```bash
npx skills add https://github.com/BofAI/skills.git
```

### Agent Wallet (Required for Signing Skills)

Some skills require wallet signature operations and are built on Agent Wallet. Before using those skills, follow the [Agent Wallet Quick Start](https://github.com/BofAI/agent-wallet?tab=readme-ov-file#quick-start) to configure your environment.

---

## Available Skills

### DeFi & DEX

- [**sunswap**](./sunswap) - SunSwap DEX integration for TRON via `sun-cli`. Supports price quotes, token swaps, liquidity and pool operations.
- [**sunperp-skill**](./sunperp-skill) - SunPerp perpetual futures trading skill for TRON. Supports market data, account queries, order placement, and position management.

### Payments & x402

- [**x402-payment**](./x402-payment) - Professional x402 payment protocol for calling paid APIs and agent resources.

### AI & Account Recharge

- [**recharge-skill**](./recharge-skill) - BANK OF AI account recharge and account query skill. Uses the remote MCP recharge service for supported payment flows.

### Data & Analytics

- [**tronscan-skill**](./tronscan-skill) - Comprehensive TRON blockchain data lookup via TronScan API. Supports accounts, transactions, tokens, blocks, and network-wide statistics.

---

## Usage Tips

When using BANK OF AI Skills, you can choose between different invocation patterns depending on your needs.

### Explicit Invocation

When you know exactly which skill is required for a task, direct the Agent to read that specific skill file.

**Best for:**
- Clear task objectives
- Deterministic execution paths
- Debugging complex workflows

**Example:**
> "Please read `skills/sunswap/SKILL.md` and check how much TRX I can get for 100 USDT on SunSwap."

### Implicit Triggering

If the skills are already within the agent's context or indexed, simply describe your goal and let the Agent match the most appropriate skill.

**Best for:**
- Natural language interactions
- Pre-loaded skills in the Agent's context
- Letting the Agent determine the optimal path

**Example:**
> "Check the current exchange rate for 100 USDT to TRX on SunSwap."

---

## Creating Skills

We follow a strict standard to ensure skills are effective and safe. Please read [**AGENTS.md**](./AGENTS.md) before contributing.

A standard skill directory includes:
- `SKILL.md`: The core instruction set.
- `examples/`: Runnable usage examples.
- `resources/`: ABIs, constants, and config files.

## Contributing

We welcome contributions from the community! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for our workflow.

## License

This repository is licensed under the [MIT License](./LICENSE).

---

<p align="center">
  <b>Built with ❤️ by Team BANK OF AI</b><br>
  <i>Empowering AI Agents with DeFi Capabilities</i>
</p>
