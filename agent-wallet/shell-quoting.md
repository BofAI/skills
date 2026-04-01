# Shell Quoting Reference for agent-wallet

Covers string types that need quoting: **passwords** and **JSON payloads**.

> Mnemonic phrases are handled by users directly in terminal, not by agents — omitted here.

---

## bash / zsh

| Value type | Recommended | Example |
|------------|-------------|---------|
| Password | `'...'` | `--password 'Abc12!@'` |
| JSON payload | `'...'` | `sign tx '{"to":"0x...","chainId":1}'` |

**Single quote containing a `'`:**
```bash
--password 'it'\''s-a-secret'
```

**Avoid `"..."` for passwords** — `!` triggers history expansion in interactive bash/zsh.

---

## PowerShell 7 (cross-platform, recommended)

| Value type | Recommended | Example |
|------------|-------------|---------|
| Password | `'...'` | `--password 'Abc12!@'` |
| JSON payload | `'...'` | `sign tx '{"to":"0x...","chainId":1}'` |

**Single quote containing a `'`:**
```powershell
--password 'it''s-a-secret'   # double the single quote
```

---

## PowerShell 5 (Windows built-in)

Passwords work the same as PS7. **JSON payloads are the problem** — PS5 strips outer quotes when passing to external programs.

| Value type | Recommended | Example |
|------------|-------------|---------|
| Password | `'...'` | `--password 'Abc12!@'` |
| JSON payload | escape inner `"` | `sign tx '{\"to\":\"0x...\",\"chainId\":1}'` |

**Alternative for JSON — use a variable:**
```powershell
$payload = '{"to":"0x...","chainId":1}'
agent-wallet sign tx $payload --network eip155:1
```

> Upgrade to PowerShell 7 if possible — JSON quoting works without workarounds.

---

## fish

| Value type | Recommended | Example |
|------------|-------------|---------|
| Password | `'...'` | `--password 'Abc12!@'` |
| JSON payload | `'...'` | `sign tx '{"to":"0x...","chainId":1}'` |

**Single quote containing a `'` — fish cannot escape inside `'...'`, concatenate instead:**
```fish
--password 'it'"'"'s-a-secret'
```

---

## cmd.exe (Windows Command Prompt)

No single quotes. JSON is unreliable. **Avoid using cmd.exe with agent-wallet** — use PowerShell instead.

| Value type | Workaround |
|------------|-----------|
| Password | `"Abc12!@"` — avoid `!` and `%` in passwords when using cmd |
| JSON payload | Escape all `"` as `\"`: `sign tx "{\"to\":\"0x...\"}"` |
| Mnemonic | `"word1 word2 ... word12"` |

---

## Quick Decision

```
Need to run agent-wallet?
├── macOS / Linux  →  bash or zsh  →  always use '...'
├── Windows        →  PowerShell 7 (preferred)  →  use '...'
│                  →  PowerShell 5  →  '...' for passwords, variable for JSON
└── Avoid cmd.exe
```
