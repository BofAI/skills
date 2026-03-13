# Skills Repository

AI Agent Skills Library - Reusable capability modules for AI agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/badge/GitHub-BofAI%2Fskills-blue)](https://github.com/BofAI/skills)

## What is a Skill?

A **Skill** is a document containing detailed instructions that teaches AI agents how to accomplish specific tasks.

**Analogy**: Like providing an "operation manual" to AI, telling it how to use tools to get work done.

```
User: "Help me swap USDT for TRX"
  ↓
AI Agent reads SunSwap Skill
  ↓
AI Agent follows SKILL.md instructions
  ↓
Calls mcp-server-tron tools
  ↓
Completes DEX trade
```

---

## Quick Start

### 1. Browse Available Skills

Currently available:
- **sunswap/** - SunSwap DEX trading skill for TRON token swaps
- **8004-skill/** - 8004 Trustless Agents (TRC-8004 / BSC implementation)
- **x402-payment/** - Coinbase-style `x402 pay` skill for TRON and BSC endpoints
- **x402-payment-demo/** - Demo of x402 payment protocol

### 2. Use a Skill

Tell your AI Agent:
```
Please read sunswap/SKILL.md and help me check how much TRX I can get for 100 USDT
```

The AI Agent will:
1. Read SKILL.md
2. Call appropriate tools following instructions
3. Return results

---

## Repository Structure

```
skills/
├── README.md              # This file - Overview
├── LICENSE                # MIT License
├── CONTRIBUTING.md        # Contribution guidelines
├── AGENTS.md              # Developer guide (how to create new skills)
├── sunswap/               # SunSwap DEX Trading skill
│   ├── README.md          # Skill description
│   ├── SKILL.md           # Main instruction file (AI Agent reads this)
│   ├── examples/          # Usage examples
│   ├── resources/         # Configuration files (contract addresses, token lists, etc.)
│   └── scripts/           # Helper scripts
├── 8004-skill/            # 8004 Trustless Agents skill
│   ├── README.md          # Skill description
│   ├── SKILL.md           # Main instruction file
│   ├── lib/               # Contract ABIs and configurations
│   ├── scripts/           # Node.js scripts for agent operations
│   ├── templates/         # Registration templates
│   └── examples/          # Usage examples
├── x402-payment/          # x402 Payment Protocol skill
│   ├── SKILL.md           # Main instruction file
│   ├── package.json       # Dependencies (run npm install before use)
│   └── src/               # TypeScript source (run via npx tsx)
└── x402-payment-demo/     # x402 Payment Demo skill
    └── SKILL.md           # Main instruction file
```

---

## Available Skills

- **[SunSwap Skills](sunswap/README.md)**: DEX Trading (TRON token swaps)
- **[8004 Trustless Agents](8004-skill/README.md)**: On-chain identity, reputation, and validation for AI agents (supports TRON & BSC)
- **[x402-payment](x402-payment/SKILL.md)**: `x402 status`, `x402 balance`, and `x402 pay` for TRON/BSC paid endpoints
- **[x402-payment-demo](x402-payment-demo/SKILL.md)**: Demo of x402 payment protocol (Protected Content Acquisition)

## How to Use Skills

### Compatible AI Agents

These Skills can be used with various AI agent platforms that support MCP (Model Context Protocol), including:
- **ClawdCode** - AI coding assistant
- **OpenCode** - Open-source AI development environment
- **OpenClaw** - AI agent framework
- And other MCP-compatible AI agents

### Installation Example (Using OpenClaw)

1. ✅ Install AI Agent (e.g., OpenClaw)
2. ✅ Install **OpenClaw Extension** 
   ```bash
   curl -fsSL https://raw.githubusercontent.com/BofAI/openclaw-extension/refs/heads/main/install.sh | bash
   ```

That's it! The installer will set up everything you need.

### For Other AI Agent Platforms

If you're using other MCP-compatible AI agents (ClawdCode, OpenCode, etc.):

1. ✅ Install your AI Agent
2. ✅ Configure MCP servers manually (see respective MCP server documentation)
3. ✅ Clone this Skills repository to your local machine:
   ```bash
   git clone https://github.com/BofAI/skills.git
   ```
4. ✅ Point your AI agent to the Skills directory or reference specific SKILL.md files when needed

---

## For Developers

### Creating a New Skill

See [AGENTS.md](AGENTS.md) for how to create new skills.

**Quick Template**:
```bash
# 1. Create directory
mkdir -p my-skill/{examples,resources,scripts}

# 2. Create SKILL.md
cat > my-skill/SKILL.md << 'EOF'
---
name: My Skill
description: What this skill does
version: 1.0.0
dependencies:
  - required-tool
tags:
  - category
---

# My Skill

## Overview
[Description]

## Usage Instructions
1. Step 1
2. Step 2
EOF
```

### Skill Specification

Each skill must include:
- ✅ **SKILL.md** - Main instruction file (with YAML frontmatter)
- ✅ **README.md** - Quick description
- ⚠️ **examples/** - Usage examples (recommended)
- ⚠️ **resources/** - Configuration files (optional)
- ⚠️ **scripts/** - Helper scripts (optional)

See [AGENTS.md](AGENTS.md) for details.

---

## FAQ

### Q: Do skills need separate installation?

**A**: ❌ No. Skills are just documents that AI agents read directly.

### Q: What's the difference between Skills and MCP Servers?

**A**: 
- **Skill** = Instruction document (teaches AI how to do something)
- **MCP Server** = Tool service (provides actual capabilities)

Skills tell AI how to use MCP Server tools.

### Q: How do I know what dependencies a skill needs?

**A**: Check the YAML frontmatter in SKILL.md:
```yaml
dependencies:
  - mcp-server-tron
```

### Q: What if AI Agent can't find the skill?

**A**: Tell it explicitly:
```
Please read sunswap/SKILL.md
```

### Q: Can I modify skills?

**A**: ✅ Yes! Edit SKILL.md directly, AI Agent will read the latest version.

---

## Contributing

Contributions of new skills are welcome!

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Related Resources

- **[AGENTS.md](AGENTS.md)** - Skill development guide
- **[OpenClaw Extension](https://github.com/BofAI/openclaw-extension)** - TRON MCP Server & Tools

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

**Repository**: [BofAI/skills](https://github.com/BofAI/skills)  
**Last Updated**: 2026-03-11  
**Maintainer**: Bank of AI Team
