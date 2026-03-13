<h1 align="center">BankOfAI Skills</h1>

<p align="center">
  <a href="https://github.com/BofAI/skills">
    <img src="https://img.shields.io/badge/GitHub-BofAI%2Fskills-blue" alt="GitHub" />
  </a>
  <a href="./LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT" />
  </a>
</p>

A curated collection of practical, DeFi-focused utility skills developed by the **BankOfAI team**. These skills enable AI agents to perform complex on-chain operations, payments, and identity management across various platforms.

> **Project Positioning:** We focus on delivering high-value DeFi utility skills that are platform-agnostic. Whether you use Claude Code, OpenClaw, Cursor, or your own agent framework, these skills provide the domain knowledge needed to interact with the TRON blockchain and beyond.

---

## Contents

- [What are BankOfAI Skills?](#what-are-bankofai-skills)
- [Installation](#installation)
  - [OpenClaw (Recommended)](#openclaw-recommended)
  - [Claude Code](#claude-code)
  - [Cursor](#cursor)
- [Available Skills](#available-skills)
  - [DeFi & DEX](#defi--dex)
  - [Identity & Reputation](#identity--reputation)
  - [Payments & x402](#payments--x402)
  - [AI & NFT](#ai--nft)
  - [Data & Analytics](#data--analytics)
- [Usage Tips](#usage-tips)
  - [Explicit Invocation](#explicit-invocation)
  - [Implicit Triggering](#implicit-triggering)
- [Creating Skills](#creating-skills)
- [Contributing](#contributing)
- [License](#license)

---

## What are BankOfAI Skills?

BankOfAI Skills are reusable, task-oriented capabilities that teach AI agents how to perform specific blockchain workflows. Each skill encapsulates domain knowledge (like SunSwap pathfinding or ERC-8004 validation) and provides step-by-step instructions for the agent to follow.

## Installation

### OpenClaw (Recommended)

OpenClaw provides the most integrated experience, automatically wiring skills and MCP dependencies.

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/openclaw-extension/refs/heads/main/install.sh | bash
```

### Claude Code

1. Clone the repository:
   ```bash
   git clone https://github.com/BofAI/skills.git /tmp/bofai-skills
   ```
2. Copy the skills to your Claude Code configuration directory for automatic discovery:
   ```bash
   mkdir -p ~/.config/claude-code/skills
   cp -r /tmp/bofai-skills/* ~/.config/claude-code/skills/
   ```
3. Claude Code will now automatically load these skills upon startup.

### Cursor

1. Clone the repository into your project's root:
   ```bash
   git clone https://github.com/BofAI/skills.git .cursor/skills
   ```
2. For project-wide availability, add the skill path to your `.cursorrules` or reference the specific `SKILL.md` file using the `@` symbol in Cursor Chat to provide the necessary context.

---

## Available Skills

### DeFi & DEX

- [**sunswap**](./sunswap) - SunSwap DEX integration for TRON. Supports price quotes, token swaps, and balance checks.

### Identity & Reputation

- [**8004-skill**](./8004-skill) - ERC-8004 implementation for AI agent identity, registration, and reputation on TRON/BSC.

### Payments & x402

- [**x402-payment**](./x402-payment) - Professional x402 payment protocol for calling paid APIs and agent resources.
- [**x402-payment-demo**](./x402-payment-demo) - A step-by-step demo of the x402 payment workflow.

### AI & NFT

- [**ainft-skill**](./ainft-skill) - Specialized skill for AINFT balance queries and recharging.

### Data & Analytics

- [**tronscan-skill**](./tronscan-skill) - Comprehensive TRON blockchain data lookup via TronScan API. Supports accounts, transactions, tokens, blocks, and network-wide statistics.

---

## Usage Tips

When using BankOfAI Skills, you can choose between different invocation patterns depending on your needs.

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
  <b>Built with ❤️ by Team BankOfAI</b><br>
  <i>Empowering AI Agents with DeFi Capabilities</i>
</p>
