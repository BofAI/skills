# Skills Repository

Reusable skills for AI agents that support MCP (Model Context Protocol).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-BofAI%2Fskills-blue)](https://github.com/BofAI/skills)

## Overview

This repository contains task-oriented skills that AI agents can load and follow. Each skill is defined by a `SKILL.md` file and may include examples, resources, and helper scripts.

The goal is simple:

- give AI agents reusable operating instructions
- connect those instructions to MCP servers and local tooling
- make common workflows repeatable across different AI platforms

## How It Works

A skill is an instruction package for an AI agent. It tells the agent:

- what the skill does
- which tools or MCP servers it depends on
- what steps to follow
- how to handle common errors

Typical flow:

1. A user asks the agent to perform a task.
2. The agent identifies the matching skill.
3. The agent reads the corresponding `SKILL.md`.
4. The agent follows the instructions and calls tools or scripts.
5. The agent returns the result.

In practice, a skill acts like an operating manual, while an MCP server provides the executable tools.

## Compatible Platforms

These skills are designed for AI agents and developer tools that support MCP, including:

- OpenClaw
- ClawdCode
- OpenCode
- other MCP-compatible AI agent platforms

## Available Skills

- [`sunswap`](./sunswap)
  SunSwap DEX skill for balances, quotes, swaps, and liquidity-related workflows.
- [`8004-skill`](./8004-skill)
  ERC-8004 skill for on-chain agent identity, trust, verification, and registration workflows.
- [`x402-payment`](./x402-payment)
  x402 payment skill for calling paid agents and paid APIs on supported chains.
- [`x402-payment-demo`](./x402-payment-demo)
  Demo workflow for end-to-end x402 protected resource access.
- [`ainft-skill`](./ainft-skill)
  Local AINFT skill for balance lookup and account-related queries.

## How To Use Skills

You can use a skill in two ways.

### Explicit Use

Tell the agent exactly which skill to read:

```text
Please read skills/sunswap/SKILL.md and tell me how much TRX I can get for 100 USDT on SunSwap.
```

This is useful when:

- you already know which skill you want
- you are debugging a workflow
- you want deterministic behavior

### Implicit Use

Describe the task and let the agent match the skill:

```text
Check how much TRX 100 USDT can swap to on SunSwap right now.
```

This is useful when:

- the skills are already installed
- the task intent is clear
- you want the agent to select the best match automatically

## Usage Examples By Skill

### `sunswap`

```text
Please read skills/sunswap/SKILL.md and check how much TRX I can get for 100 USDT on SunSwap.
```

### `8004-skill`

```text
Please read skills/8004-skill/SKILL.md and look up the on-chain registration details for agent 1:8 on TRON mainnet.
```

### `x402-payment`

```text
Please read skills/x402-payment/SKILL.md and call this paid agent endpoint using x402.
```

### `x402-payment-demo`

```text
Please read skills/x402-payment-demo/SKILL.md and run a demo x402 payment flow end to end.
```

### `ainft-skill`

```text
Please read skills/ainft-skill/SKILL.md and check the current AINFT balance and recent orders for this account.
```

## Installation

### Option 1: OpenClaw Extension

If you use OpenClaw, the fastest path is to install the OpenClaw extension:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/openclaw-extension/refs/heads/main/install.sh | bash
```

The extension helps with:

- cloning the skills repository
- setting up common MCP servers
- configuring supported skills

### Option 2: Manual Installation

For ClawdCode, OpenCode, or any other MCP-compatible platform:

1. Install your AI agent platform.
2. Configure the MCP servers required by your workflows.
3. Clone this repository.
4. Point your agent to the `skills/` directory or reference a specific `SKILL.md` directly.

```bash
git clone https://github.com/BofAI/skills.git
cd skills/skills
```

## Quick Start

1. Install an MCP-capable AI agent such as OpenClaw.
2. Clone this repository or install the OpenClaw extension.
3. Pick a skill from the list above.
4. Ask the agent to read that skill's `SKILL.md`.
5. Provide the required parameters in your prompt.

Example:

```text
Please read skills/x402-payment/SKILL.md and use it to call this paid endpoint with x402 on mainnet.
```

## Creating A New Skill

Read [AGENTS.md](./AGENTS.md) before creating a new skill. It defines the expected structure and writing standards.

Recommended minimum layout:

```bash
mkdir -p my-skill/{examples,resources,scripts}
```

Then create `my-skill/SKILL.md`:

```md
---
name: My Skill
description: What this skill does
version: 1.0.0
---

# My Skill

## Overview
[Description]

## Usage Instructions
1. Step 1
2. Step 2
```

A good skill should include:

- `SKILL.md`
- a clear overview
- dependency and prerequisite notes
- usage examples
- error-handling guidance when relevant

## Repository Structure

```text
skills/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── AGENTS.md
├── sunswap/
├── 8004-skill/
├── ainft-skill/
├── x402-payment/
└── x402-payment-demo/
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

This repository is released under the [MIT License](./LICENSE).
