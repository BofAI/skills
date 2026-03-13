# Skills Repository

Reusable skills for OpenClaw and other MCP-capable AI agents.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-BofAI%2Fskills-blue)](https://github.com/BofAI/skills)

## 1. Overview

This is the skills repository used by the BofAI/OpenClaw ecosystem. It contains the installable skill packages pulled by OpenClaw Extension and referenced directly by other local AI agent setups.

Each skill lives in its own directory and is centered around a `SKILL.md` file, with optional `scripts/`, `resources/`, and `examples/` directories when the workflow needs them.

## 2. Available Skills

Current skills in this repository:

| Skill | Description |
|-------|-------------|
| [`sunswap`](./sunswap) | SunSwap DEX skill for balance checks, quotes, pricing, swaps, and other token workflows on TRON. |
| [`x402-payment`](./x402-payment) | x402 payment skill for calling paid agents and APIs on supported chains. |
| [`x402-payment-demo`](./x402-payment-demo) | Demo skill for an end-to-end x402 protected resource access flow. |
| [`ainft-skill`](./ainft-skill) | Local AINFT skill for balance and order queries. |

## 3. Quick Start

This section uses `OpenClaw + OpenClaw Extension`, which is the primary installation path for this repository.

### 3.1 Installation

Install the OpenClaw Extension first. It installs the integration layer, connects MCP servers, and installs the skills from this repository.

OpenClaw Extension:

- Repository: [BofAI/openclaw-extension](https://github.com/BofAI/openclaw-extension)
- Install script:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/openclaw-extension/refs/heads/main/install.sh | bash
```

If you prefer to inspect the installer before running it:

```bash
git clone https://github.com/BofAI/openclaw-extension.git
cd openclaw-extension
./install.sh
```

### 3.2 Verification

After installation, verify that the skills repository is available and that your agent can read a skill.

By default, the OpenClaw Extension installs skills to either `~/.openclaw/skills` or `.openclaw/skills` in the current workspace.

Check the local skills directory:

```bash
ls ~/.openclaw/skills
```

You should see entries such as:

- `sunswap`
- `8004-skill`
- `x402-payment`
- `x402-payment-demo`
- `ainft-skill`

Then verify in OpenClaw by asking a direct prompt such as:

```text
Read the sunswap skill and tell me what this skill can do.
```

### 3.3 First Use

Start with a narrow, read-only workflow.

Recommended first prompt:

```text
Read the sunswap skill and help me check how much TRX I can get for 100 USDT on SunSwap right now.
```

Other simple first-run examples:

```text
Read the 8004-skill and look up the on-chain registration details for agent 1:8 on TRON mainnet.
```

```text
Read the x402-payment skill and use it to call this paid endpoint with x402 on nile.
```

## 4. Installation and Usage on Other Platforms

If you are not using OpenClaw, the common pattern is:

1. install or configure the AI agent
2. configure required MCP servers for your workflow
3. clone this repository locally
4. let the agent read the target `SKILL.md`

If a platform does not support a dedicated skills directory, explicitly reference the `SKILL.md` file in your prompt.

### 4.1 Claude Code

Clone the repository locally:

```bash
git clone https://github.com/BofAI/skills.git ~/.bofai/skills
```

Then use explicit prompts that point to a skill file, for example:

```text
Please read ~/.bofai/skills/skills/sunswap/SKILL.md and check how much TRX I can get for 100 USDT.
```

If you need blockchain or payment workflows, make sure the corresponding MCP servers and credentials are already configured in your local environment.

### 4.2 Claude Desktop

Use Claude Desktop only if your local setup can expose the needed MCP servers to it. Then clone the repository:

```bash
git clone https://github.com/BofAI/skills.git ~/.bofai/skills
```

Recommended usage pattern:

- configure MCP servers in the platform's local integration entry
- keep this repository on disk
- explicitly tell the agent which `SKILL.md` to read

Example prompt:

```text
Please read ~/.bofai/skills/skills/8004-skill/SKILL.md and summarize how to query an agent on TRON mainnet.
```

### 4.3 Cursor

Clone the repository:

```bash
git clone https://github.com/BofAI/skills.git ~/.bofai/skills
```

Then either:

- point Cursor to the local skill file in chat
- or open the repository and ask it to read `skills/<skill-name>/SKILL.md`

Example:

```text
Please read skills/x402-payment/SKILL.md and explain the required environment variables.
```

### 4.4 OpenClaw

OpenClaw is the recommended path because the extension already wires skills and common MCP dependencies together.

Install via OpenClaw Extension:

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/openclaw-extension/refs/heads/main/install.sh | bash
```

Then ask for a skill explicitly or describe the task in natural language.

### 4.5 Manual Installation (Generic)

If your platform is MCP-compatible but has no dedicated installer, use the generic flow:

```bash
git clone https://github.com/BofAI/skills.git ~/.bofai/skills
```

Then:

1. configure required MCP servers yourself
2. point the platform to `~/.bofai/skills/skills` if it supports a skills directory
3. otherwise, reference `SKILL.md` files directly in prompts

Generic example:

```text
Please read ~/.bofai/skills/skills/x402-payment-demo/SKILL.md and run the demo flow on nile.
```

## 5. Usage Tips

There are two main ways to use a skill.

### 5.1 Explicit Invocation

Tell the agent exactly which skill file to read.

Example:

```text
Please read skills/sunswap/SKILL.md and check how much TRX 100 USDT can swap to on SunSwap.
```

Use explicit invocation when:

- you already know the target skill
- you want deterministic behavior
- you are debugging a workflow

### 5.2 Implicit Triggering

Describe the task and let the agent match the appropriate skill.

Example:

```text
Check how much TRX 100 USDT can swap to on SunSwap right now.
```

Use implicit triggering when:

- the skills are already installed
- the request clearly maps to one workflow
- you want the agent to select the best skill automatically

## 6. Create a New Skill

Read [AGENTS.md](./AGENTS.md) before creating a new skill. It defines the expected structure, frontmatter format, and writing guidelines.

Recommended minimum layout:

```bash
mkdir -p my-skill/{examples,resources,scripts}
```

Create `my-skill/SKILL.md`:

```md
---
name: My Skill
description: Brief description of what the skill does
version: 1.0.0
tags:
  - category
---

# My Skill

## Overview
[What this skill does]

## Usage Instructions
1. Step 1
2. Step 2
3. Step 3
```

A good skill should include:

- a clear overview
- prerequisites and dependencies
- step-by-step usage instructions
- examples
- error handling guidance
- security notes when relevant

## 7. Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

Typical contribution flow:

1. fork and clone the repository
2. create or update a skill
3. test the skill with an AI agent
4. verify examples and scripts
5. submit a pull request with testing notes

## 8. License

This repository is released under the [MIT License](./LICENSE).
