# x402 Payment Skill

Pay x402-protected HTTP resources with `x402-cli`. Payment execution no longer uses bundled TypeScript scripts or a skill-local SDK installation.

Requires Node.js 20+ and npm.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/main/x402-payment/install.sh | sh
```

The installer installs the skill and verifies `@bankofai/x402-cli@1.0.1` (x402 SDK 1.0.1 and Gateway 1.0.1) globally. After installation:

```bash
x402-cli --version
x402-cli pay https://api.example.com/protected --dry-run --json
```

See [SKILL.md](SKILL.md) for the payment workflow and safety rules.
