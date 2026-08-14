# Twitter Digest First-Install Authorization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a fresh Twitter Digest installation use the pinned BofAI xurl and guide an unconfigured operator through App registration, browser OAuth, default-user selection, and X Chat key recovery.

**Architecture:** Keep the deliverable at five files by implementing the interactive setup in the existing POSIX `install.sh`. Exercise it through a temporary end-to-end shell harness with isolated homes and stubbed npm/xurl processes, then remove the harness before release.

**Tech Stack:** POSIX shell, npm package installation, BofAI xurl CLI.

## Global Constraints

- Install exactly `@bankofai/xurl@1.3.2-beta.3`; never install or invoke `@xdevplatform/xurl` or a global xurl.
- Preserve `~/.xurl` and keep the final `twitter-digest` directory to `SKILL.md`, `agents/openai.yaml`, `bin/xurl`, `install.sh`, and `uninstall.sh`.
- Existing OAuth2 authorization must remain non-interactive.
- New OAuth2 authorization must run in a real Terminal and open the browser unless headless mode is required.
- xurl can restore existing X Chat keys but cannot create or register new keys.

---

### Task 1: Pin and verify BofAI npm provenance

**Files:**
- Modify: `twitter-digest/install.sh`
- Test temporarily: `/tmp/twitter-digest-install-auth-test.sh`

**Interfaces:**
- Consumes: npm's installed package directory under `$XURL_NPM_ROOT/node_modules/@bankofai/xurl`.
- Produces: a verified `$PACKAGE_DIR/bin/xurl`; installation stops before replacing the current skill when metadata or executable checks fail.

- [ ] **Step 1: Write the failing integration scenarios**

Create a temporary POSIX shell harness that runs the real installer with an isolated `HOME`, a stub `npm`, and a generated xurl executable. Assert that an npm tree with `name: @xdevplatform/xurl` or a version other than `1.3.2-beta.3` fails and leaves the target absent.

- [ ] **Step 2: Run the scenarios and verify RED**

Run:

```bash
/bin/sh /tmp/twitter-digest-install-auth-test.sh provenance
```

Expected: the wrong-name scenario incorrectly reaches installation because the current installer checks only the executable version.

- [ ] **Step 3: Implement exact metadata validation**

After npm installation, read the installed package metadata with npm/Node from the exact `@bankofai/xurl` directory and require both values:

```text
name=@bankofai/xurl
version=1.3.2-beta.3
```

Retain the existing `xurl version` and X Chat availability checks. Do not add a fallback package or global executable lookup.

- [ ] **Step 4: Run the scenarios and verify GREEN**

Run the provenance scenario again and require zero failures.

- [ ] **Step 5: Commit**

```bash
git add twitter-digest/install.sh
git commit -m "fix(twitter-digest): verify bundled xurl provenance"
```

### Task 2: Add first-install OAuth guidance

**Files:**
- Modify: `twitter-digest/install.sh`
- Test temporarily: `/tmp/twitter-digest-install-auth-test.sh`

**Interfaces:**
- Consumes: the installed target's `bin/xurl`, terminal input, `auth apps list`, `auth status`, `auth oauth2`, `auth default`, and `whoami`.
- Produces: `configure_installed_xurl XURL_PATH`, which returns success only after an existing or newly authorized OAuth2 identity passes `whoami`.

- [ ] **Step 1: Add failing end-to-end scenarios**

Cover these isolated states:

```text
authorized       -> whoami succeeds; oauth2 is never called
one app          -> that app is authorized without an app-selection prompt
several apps     -> the selected numbered app is authorized
no apps          -> hidden Client Secret prompt, apps add, then oauth2
skip configure   -> no auth command is called
oauth failure    -> installed skill remains, configuration exits non-zero with a recovery command
```

- [ ] **Step 2: Run the scenarios and verify RED**

Run:

```bash
/bin/sh /tmp/twitter-digest-install-auth-test.sh auth
```

Expected: scenarios fail because the current installer only prints manual commands.

- [ ] **Step 3: Implement the minimal interactive functions**

Add POSIX shell functions with these responsibilities:

```text
prompt_value LABEL DEFAULT     read from /dev/tty when available, otherwise stdin
prompt_secret LABEL            disable terminal echo while reading
configured_apps XURL           return only entries marked [app config]
oauth_username XURL APP        return a non-(none) oauth2 username
select_or_register_app XURL    reuse one app, select among many, or register a prompted app
configure_installed_xurl XURL  reuse whoami or authorize the selected app and verify whoami
```

Run `auth oauth2 --app APP`; add `--headless` only when no local browser session is available. After OAuth, obtain the username from `auth status --app APP`, run `auth default APP USERNAME`, and require `whoami` to succeed.

- [ ] **Step 4: Configure once after all targets are installed**

Record the first installed target's bundled xurl and call configuration after the Codex/Claude/all installation loop. This prevents `--client all` from launching OAuth twice. Keep `--skip-configure` as a complete bypass.

- [ ] **Step 5: Run the scenarios and verify GREEN**

Run the auth scenario again and require zero failures and no secrets in captured output.

- [ ] **Step 6: Commit**

```bash
git add twitter-digest/install.sh
git commit -m "feat(twitter-digest): guide first-install OAuth"
```

### Task 3: Add X Chat key recovery and operator documentation

**Files:**
- Modify: `twitter-digest/install.sh`
- Modify: `twitter-digest/SKILL.md`
- Test temporarily: `/tmp/twitter-digest-install-auth-test.sh`

**Interfaces:**
- Consumes: authenticated xurl and `chat keys status` output.
- Produces: no-op for a present local key; interactive `chat keys restore` offer otherwise; official-client instruction when restore cannot provide a key.

- [ ] **Step 1: Add failing key scenarios**

Assert that a present local key skips restore, an absent key offers restore once, and a failed restore explains that the account must first enable X Chat in an official X client.

- [ ] **Step 2: Run the key scenarios and verify RED**

Run:

```bash
/bin/sh /tmp/twitter-digest-install-auth-test.sh chat-keys
```

Expected: scenarios fail because the installer currently prints only `chat keys status` and `chat keys restore` commands.

- [ ] **Step 3: Implement key recovery**

After verified OAuth, run `chat keys status`. Match `local keys: present` as success. Otherwise ask whether to restore now, invoke `chat keys restore` directly so xurl owns PIN entry, and verify status again. If no key is available, print the official-client prerequisite without claiming xurl can initialize one.

- [ ] **Step 4: Update installation documentation**

In `SKILL.md`, state that installation automatically reuses or requests OAuth, remains pinned to the BofAI package, and can restore but not create X Chat keys.

- [ ] **Step 5: Run the scenarios and verify GREEN**

Run the key scenario and the complete temporary harness; require zero failures.

- [ ] **Step 6: Commit**

```bash
git add twitter-digest/install.sh twitter-digest/SKILL.md
git commit -m "feat(twitter-digest): guide Chat key recovery"
```

### Task 4: Release verification

**Files:**
- Verify: `twitter-digest/SKILL.md`
- Verify: `twitter-digest/agents/openai.yaml`
- Verify: `twitter-digest/install.sh`
- Verify: `twitter-digest/uninstall.sh`
- Remove: `/tmp/twitter-digest-install-auth-test.sh`

**Interfaces:**
- Consumes: completed installer and documentation.
- Produces: pushed branch and a clean local installation using the exact published BofAI xurl.

- [ ] **Step 1: Run complete verification**

```bash
/bin/sh /tmp/twitter-digest-install-auth-test.sh all
sh -n twitter-digest/install.sh twitter-digest/uninstall.sh
uv run --with pyyaml python /Users/bobo/.codex/skills/.system/skill-creator/scripts/quick_validate.py twitter-digest
git diff --check
```

- [ ] **Step 2: Run a real package acquisition without changing authorization**

Use an isolated temporary skills directory and `--skip-configure`. Verify package metadata, `bin/xurl version`, X Chat help, and the exact five-file result.

- [ ] **Step 3: Remove the temporary harness and inspect the diff**

Delete `/tmp/twitter-digest-install-auth-test.sh`; confirm no test file or extra runtime dependency appears under `twitter-digest`.

- [ ] **Step 4: Push and refresh the local skill**

Push the release branch, reinstall the Codex target with `--skip-configure` so existing authorization and Chat keys remain untouched, and compare installed files with the source.
