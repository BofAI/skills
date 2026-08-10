# Twitter Digest Post-Install Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make standard Codex and Claude installations automatically hand off to the existing unified X API and X Chat configuration wizard while preserving non-interactive test and custom-install behavior.

**Architecture:** `install.sh` owns the environment-facing default and forwards one explicit Python installer flag. `scripts/install.py` owns post-copy policy, invokes the installed `configure_all.py`, and formats failures without rolling back the installed Skill. The unified configuration implementation remains the single authority for credential validation and prompts.

**Tech Stack:** POSIX shell, Python 3.10+, `unittest`, existing twitter-digest installer and unified configuration scripts.

## Global Constraints

- Ship as `v1.5.14-beta.14`; never change the published `v1.5.14-beta.13` tag.
- Automatic configuration is enabled only for standard installs without `--skills-dir` and without `--dry-run`.
- `TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL=0` disables automatic configuration.
- Invoke the installed `scripts/configure_all.py`; never duplicate OAuth or X Chat validity rules in the installer.
- A configuration failure leaves the installed Skill and restored `.state` intact.
- Never collect a digest, request secrets in Agent chat, or save the X Chat passcode during installation.

---

### Task 1: Post-install configuration policy

**Files:**
- Modify: `twitter-digest/scripts/install.py`
- Test: `twitter-digest/tests/test_security_contract.py`

**Interfaces:**
- Consumes: installed Skill path returned by `install_skill`, selected client name, `--skills-dir`, `--dry-run`, and a new `--configure-after-install` flag.
- Produces: `run_post_install_configuration(target: Path, client: str, enabled: bool, custom_skills_dir: bool, dry_run: bool) -> None`.

- [ ] **Step 1: Write failing policy and invocation tests**

Add tests that assert standard enabled installs invoke the installed script and that disabled, custom-directory, and dry-run calls do not invoke a subprocess:

```python
def test_post_install_configuration_invokes_installed_unified_wizard(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "twitter-digest"
        script = target / "scripts" / "configure_all.py"
        script.parent.mkdir(parents=True)
        script.touch()
        with mock.patch.object(install.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
            install.run_post_install_configuration(target, "codex", True, False, False)
        run.assert_called_once_with([sys.executable, str(script)], check=False)
```

Also call the function with `enabled=False`, `custom_skills_dir=True`, and `dry_run=True`, asserting `subprocess.run` is not called.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
python3 -m unittest twitter-digest.tests.test_security_contract.SecurityContractTests.test_post_install_configuration_invokes_installed_unified_wizard
```

Expected: `AttributeError` because `run_post_install_configuration` does not exist.

- [ ] **Step 3: Implement the minimal post-install policy**

Add the parser flag and helper:

```python
import subprocess

parser.add_argument("--configure-after-install", action="store_true")

def run_post_install_configuration(
    target: Path,
    client: str,
    enabled: bool,
    custom_skills_dir: bool,
    dry_run: bool,
) -> None:
    if not enabled or custom_skills_dir or dry_run:
        return
    script = target / "scripts" / "configure_all.py"
    completed = subprocess.run([sys.executable, str(script)], check=False)
    if completed.returncode != 0:
        command = f"python3 {display_path(target / 'scripts' / 'run_daily_digest.py')} --configure"
        raise SystemExit(f"X API and X Chat configuration did not complete. The Skill remains installed. Retry with: {command}")
```

Call it at the end of `main()` after installation, state restoration, and Claude settings updates.

Also call `main()` with mocked `install_skill` and `run_post_install_configuration`, record both calls, and assert installation occurs first. Add a failure test that uses a nonzero return code, asserts the installed target still exists, and checks the `SystemExit` text contains `The Skill remains installed` but not `Traceback`.

- [ ] **Step 4: Run focused and complete security tests**

Run:

```bash
python3 -m unittest twitter-digest.tests.test_security_contract
```

Expected: all security contract tests pass.

- [ ] **Step 5: Commit Task 1**

```bash
git add twitter-digest/scripts/install.py twitter-digest/tests/test_security_contract.py
git commit -m "feat(twitter-digest): configure standard installs"
```

---

### Task 2: Shell installer default and opt-out

**Files:**
- Modify: `twitter-digest/install.sh`
- Test: `twitter-digest/tests/test_security_contract.py`

**Interfaces:**
- Consumes: `TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL`, defaulting to `1` and interpreted by the existing `truthy` shell helper.
- Produces: `--configure-after-install` for the Python installer and forwards the environment setting into a spawned macOS Terminal child.

- [ ] **Step 1: Write failing shell-contract tests**

Add a test that reads `install.sh` and requires all three strings:

```python
def test_shell_installer_enables_and_forwards_post_install_configuration(self) -> None:
    installer = (SCRIPTS.parent / "install.sh").read_text(encoding="utf-8")
    self.assertIn('TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL:-1', installer)
    self.assertIn('TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL=', installer)
    self.assertIn('--configure-after-install', installer)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python3 -m unittest twitter-digest.tests.test_security_contract.SecurityContractTests.test_shell_installer_enables_and_forwards_post_install_configuration
```

Expected: failure because the shell installer has no post-install configuration setting.

- [ ] **Step 3: Implement shell forwarding**

Add:

```sh
CONFIGURE_AFTER_INSTALL="${TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL:-1}"
```

Forward the variable into the Terminal child command, and append the Python flag only when enabled:

```sh
if truthy "$CONFIGURE_AFTER_INSTALL"; then
  args="$args --configure-after-install"
fi
```

- [ ] **Step 4: Run the security tests and shell syntax check**

Run:

```bash
sh -n twitter-digest/install.sh
python3 -m unittest twitter-digest.tests.test_security_contract
```

Expected: shell syntax is valid and all security tests pass.

- [ ] **Step 5: Commit Task 2**

```bash
git add twitter-digest/install.sh twitter-digest/tests/test_security_contract.py
git commit -m "feat(twitter-digest): enable setup after curl install"
```

---

### Task 3: Release documentation and end-to-end verification

**Files:**
- Modify: `twitter-digest/SKILL.md`
- Modify: `twitter-digest/README.md`
- Modify: `twitter-digest/tests/test_security_contract.py`

**Interfaces:**
- Consumes: the public `v1.5.14-beta.14` installation URL and `TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL=0` opt-out.
- Produces: accurate Codex/Claude commands and documented post-install behavior.

- [ ] **Step 1: Update the version contract test to beta.14**

Rename the version test and require `v1.5.14-beta.14` in `install.sh`, `README.md`, and `SKILL.md`, while rejecting `v1.5.14-beta.13` from the active install instructions.

- [ ] **Step 2: Run the version test and verify RED**

Run:

```bash
python3 -m unittest twitter-digest.tests.test_security_contract.SecurityContractTests.test_beta14_installer_and_docs_are_pinned
```

Expected: failure until active version references are updated.

- [ ] **Step 3: Update version and behavior documentation**

Change public URLs to `v1.5.14-beta.14`. Document that standard installs immediately run the unified configuration check, valid state is reused, custom `--skills-dir` and dry runs skip configuration, and this opt-out is available:

```bash
TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL=0
```

- [ ] **Step 4: Run the complete automated verification**

Run:

```bash
python3 -m compileall -q twitter-digest/scripts
sh -n twitter-digest/install.sh
python3 -m unittest discover -s twitter-digest/tests -p 'test_*.py'
uv run --with pyyaml python /Users/bobo/.codex/skills/.system/skill-creator/scripts/quick_validate.py twitter-digest
git diff --check
```

Expected: compilation and shell syntax succeed, all tests pass, Skill validation succeeds, and no whitespace errors are reported.

- [ ] **Step 5: Verify installation boundaries locally**

Run a public-style local repository custom install with configuration enabled. `--skills-dir` must suppress the handoff:

```bash
temp_skills_dir=$(mktemp -d)
env TWITTER_DIGEST_OPEN_TERMINAL=0 \
    TWITTER_DIGEST_INSTALL_TAG=twitter-digest-beta14 \
    TWITTER_DIGEST_INSTALL_REPO=file:///Users/bobo/code/skills/skills \
    TWITTER_DIGEST_INSTALL_CLIENT=codex \
    /bin/sh twitter-digest/install.sh --skills-dir "$temp_skills_dir"
test -f "$temp_skills_dir/twitter-digest/SKILL.md"
```

Reinstall standard Codex and Claude targets with explicit opt-out so existing credentials remain untouched during release verification:

```bash
env TWITTER_DIGEST_OPEN_TERMINAL=0 TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL=0 \
    TWITTER_DIGEST_INSTALL_TAG=twitter-digest-beta14 \
    TWITTER_DIGEST_INSTALL_REPO=file:///Users/bobo/code/skills/skills \
    TWITTER_DIGEST_INSTALL_CLIENT=codex \
    /bin/sh twitter-digest/install.sh

env TWITTER_DIGEST_OPEN_TERMINAL=0 TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL=0 \
    TWITTER_DIGEST_INSTALL_TAG=twitter-digest-beta14 \
    TWITTER_DIGEST_INSTALL_REPO=file:///Users/bobo/code/skills/skills \
    TWITTER_DIGEST_INSTALL_CLIENT=claude \
    TWITTER_DIGEST_ALLOW_CLAUDE_COMMANDS=1 \
    TWITTER_DIGEST_ALLOW_CLAUDE_STATE_READ=1 \
    /bin/sh twitter-digest/install.sh
```

The automated `subprocess.run` test from Task 1 is the clean isolation proof for the configuration handoff; do not prompt for or print real credentials during test execution.

- [ ] **Step 6: Commit Task 3**

```bash
git add twitter-digest/SKILL.md twitter-digest/README.md twitter-digest/tests/test_security_contract.py
git commit -m "docs(twitter-digest): publish beta14 setup flow"
```

- [ ] **Step 7: Publish only after explicit user approval**

Push `twitter-digest-beta14`, create annotated tag `v1.5.14-beta.14`, push the tag, fetch the public raw installer, and perform a temporary opt-out installation before handing off the final `curl` commands.
