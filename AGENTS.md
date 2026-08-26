# Agent Guidelines: Skills Repository

This document provides essential information for AI agents working on skills in this repository.

---

## 📁 Repository Structure

```
skills/
├── AGENTS.md                    # This file - development guidelines
├── sunswap/                     # SunSwap DEX trading skill
│   ├── SKILL.md                 # Main skill definition
│   ├── examples/                # Usage examples
│   ├── resources/               # Configuration files
│   └── scripts/                 # Helper scripts
└── [other-skills]/              # Future skills
```

---

## 🎯 What is a Skill?

A **skill** is a reusable capability that AI agents can use to accomplish specific tasks. Each skill:

- **Encapsulates domain knowledge** (e.g., how to use SunSwap DEX)
- **Provides step-by-step instructions** for AI agents
- **Includes examples** showing common usage patterns
- **May depend on external tools** (e.g., MCP servers)

---

## 📝 Skill File Format

### SKILL.md Structure

Every skill must have a `SKILL.md` file with this format:

```markdown
---
name: Skill Name
description: Brief description of what the skill does
version: 1.0.0
dependencies:
  - dependency-1
  - dependency-2
tags:
  - tag1
  - tag2
---

# Skill Name

## Overview
[What this skill does]

## Prerequisites
[What needs to be set up before using this skill]

## Usage Instructions
[Step-by-step guide for AI agents]

## Examples
[Links to example files or inline examples]

## Error Handling
[Common errors and how to handle them]

## Security Considerations
[Important security notes]
```

### YAML Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ | Human-readable skill name |
| `description` | ✅ | Brief description (1-2 sentences) |
| `version` | ✅ | Repository release version from the root `VERSION` file |
| `dependencies` | ⚠️ | List of required tools/servers (e.g., mcp-server-tron) |
| `tags` | ⚠️ | Searchable tags for skill discovery |

---

## 🗂 Skill Directory Structure

### Versioning

All skills are released together and must use the exact version in the root `VERSION` file. Skill
versions do not track their external CLI or SDK dependencies. See [VERSIONING.md](./VERSIONING.md)
and run `sh scripts/check_versions.sh` after changing a version.

### Required Files

- **SKILL.md** - Main skill definition (required)

### Optional Directories

- **examples/** - Usage examples (recommended)
  - Use `.md` files for documentation
  - Include complete, runnable examples
  
- **resources/** - Configuration files (optional)
  - JSON files for addresses, ABIs, constants
  - Should be referenced in SKILL.md
  
- **scripts/** - Helper scripts (optional)
  - Python, JavaScript, or shell scripts
  - Should be documented in SKILL.md

---

## 🛠 Creating a New Skill

### Step 1: Create Directory

```bash
mkdir -p skills/my-skill/{examples,resources,scripts}
```

### Step 2: Create SKILL.md

```bash
cat > skills/my-skill/SKILL.md << 'EOF'
---
name: My Skill
description: What this skill does
version: <value from root VERSION>
tags:
  - category
---

# My Skill

## Overview
[Description]

## Usage Instructions
1. Step 1
2. Step 2
3. Step 3
EOF
```

### Step 3: Add Examples

```bash
cat > skills/my-skill/examples/basic_usage.md << 'EOF'
# Basic Usage Example

## Scenario
[What this example demonstrates]

## Steps
1. [Step 1 with code]
2. [Step 2 with code]
EOF
```

### Step 4: Test the Skill

- Read SKILL.md as an AI agent would
- Follow the instructions step-by-step
- Verify examples work as expected

---

## 📚 Writing Effective Skills

### Best Practices

#### 1. **Be Specific and Actionable**
❌ Bad: "Use the tool to get data"
✅ Good: "Call `read_contract` with contractAddress='TXX...' and functionName='balanceOf'"

#### 2. **Include Complete Examples**
- Show full tool calls with all parameters
- Include expected outputs
- Cover error cases

#### 3. **Document Dependencies Clearly**
```markdown
## Prerequisites

This skill requires:
- `mcp-server-tron` configured in your MCP client
- TRON wallet with private key set in environment
- Testnet TRX for gas fees
```

#### 4. **Use Code Blocks for Tool Calls**
```markdown
## Step 1: Get Price Quote

Use the `read_contract` tool:

\`\`\`json
{
  "contractAddress": "TKzxdSv2FZKQrEqkKVgp5DcwEXBEKMg2Ax",
  "functionName": "getAmountsOut",
  "args": [100000000, ["TUSDT...", "TWTRX..."]],
  "network": "mainnet"
}
\`\`\`
```

#### 5. **Handle Errors Gracefully**
```markdown
## Common Errors

### Error: "Insufficient allowance"
**Cause**: Token not approved for Router
**Solution**: Call `approve` function first (see example)

### Error: "Slippage too high"
**Cause**: Price moved beyond acceptable range
**Solution**: Increase slippage tolerance or retry
```

---

## 🔍 Skill Discovery

AI agents discover skills by:
1. Reading `SKILL.md` files in the skills directory
2. Matching tags to user requests
3. Following instructions in the skill

### Tagging Guidelines

Use descriptive, searchable tags:

```yaml
tags:
  - defi          # Category
  - dex           # Subcategory
  - swap          # Action
  - tron          # Blockchain
  - sunswap       # Specific protocol
```

---

## 🧪 Testing Skills

### Manual Testing Checklist

- [ ] SKILL.md has valid YAML frontmatter
- [ ] SKILL.md version matches the root VERSION file
- [ ] All dependencies are documented
- [ ] Instructions are clear and step-by-step
- [ ] Examples run without errors
- [ ] Resource files are valid (JSON, etc.)
- [ ] Scripts execute successfully

### Testing with AI Agents

1. **Load the skill** in your AI agent environment
2. **Ask a relevant question** (e.g., "How do I swap tokens on SunSwap?")
3. **Verify the agent**:
   - Finds the correct skill
   - Follows the instructions
   - Uses the right tools
   - Handles errors properly

---

## 🔐 Security Guidelines

### For Skill Authors

- **Never hardcode private keys** in examples or scripts
- **Always use environment variables** for sensitive data
- **Include slippage protection** in DeFi examples
- **Warn about testnet vs mainnet** usage
- **Document gas/fee requirements**

### Example Security Note

```markdown
> [!WARNING]
> **Slippage Protection**: Always set `amountOutMin` to prevent 
> sandwich attacks. Recommended slippage: 0.5-1% for stablecoins, 
> 1-3% for volatile tokens.
```

---

## 📖 Documentation Standards

### Markdown Formatting

- Use **headers** for structure (##, ###)
- Use **code blocks** for tool calls and outputs
- Use **tables** for parameter lists
- Use **alerts** for important notes:
  - `> [!NOTE]` - General information
  - `> [!WARNING]` - Important warnings
  - `> [!CAUTION]` - Critical security issues

### Code Examples

Always include:
- **Context**: What the code does
- **Input**: Parameters and their values
- **Output**: Expected result
- **Error handling**: What can go wrong

---

## 🤝 Contributing Skills

### Contribution Workflow

1. **Synchronize `develop`** with the upstream repository
2. **Create `feature/<short_description>`** from `develop`
3. **Create or update the Skill** following this guide
4. **Test thoroughly** with AI agents
5. **Document dependencies** clearly
6. **Submit a pull request to `develop`**

Do not push directly to `develop` or `main`. Release and hotfix work follows
[BRANCHING.md](./BRANCHING.md).

### Review Criteria

- ✅ Clear, actionable instructions
- ✅ Complete examples
- ✅ Proper error handling
- ✅ Security considerations documented
- ✅ Dependencies listed
- ✅ Valid YAML frontmatter

---

## 🔗 Related Resources

| Resource | Description |
|----------|-------------|
| [BRANCHING.md](./BRANCHING.md) | Development, release, and hotfix workflow |
| [mcp-server-tron](../mcp-server-tron/) | TRON blockchain MCP server |
| [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) | Project-wide development guide |
| [agents.md](../agents.md) | Agent architecture documentation |

---

## 💡 Skill Ideas

Future skills to consider:
- **Token Transfer** - Simple TRC20 transfers
- **NFT Minting** - Create and mint NFTs
- **Staking** - Stake tokens in DeFi protocols
- **Governance** - Vote on DAO proposals
- **Analytics** - Query blockchain data

---

## ❓ FAQ

### Q: Can a skill depend on another skill?
A: Yes, list it in `dependencies` and reference it in instructions.

### Q: How do I version a skill?
A: Use the repository release in the root `VERSION` file. All skills advance together; dependency
versions remain independent.

### Q: Can I use external APIs in a skill?
A: Yes, but document them clearly in prerequisites.

### Q: How do I handle network-specific addresses?
A: Use resource files (JSON) with network-specific configs.

---

## 🆘 Getting Help

- **Check existing skills** for examples (e.g., `sunswap/`)
- **Read SKILL.md format** carefully
- **Test with AI agents** before finalizing
- **Ask for review** if unsure

---

**Last Updated**: 2026-08-26
**Maintainer**: Bank of AI Team
