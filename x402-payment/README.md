# x402 Payment Skill

Pay x402-protected HTTP resources with `x402-cli`. Payment execution no longer uses bundled TypeScript scripts or a skill-local SDK installation.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/BofAI/skills/main/x402-payment/install.sh | sh
```

The installer installs the skill and `@bankofai/x402-cli@1.0.1-beta.0` globally. After installation:

```bash
x402-cli --version
x402-cli pay https://api.example.com/protected --dry-run --json
```

See [SKILL.md](SKILL.md) for the payment workflow and safety rules.
