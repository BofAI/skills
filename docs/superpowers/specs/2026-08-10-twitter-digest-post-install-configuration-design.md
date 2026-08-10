# Twitter Digest Post-Install Configuration Design

## Goal

Make a standard `twitter-digest` installation finish setup as part of the same user flow. After copying or upgrading the Skill, the installer checks the saved X API and X Chat configuration through the existing unified configuration wizard. Complete configuration is reused; missing or invalid configuration starts the secure Terminal flow.

This change ships as `v1.5.14-beta.14`. It does not modify the published `v1.5.14-beta.13` tag.

## Selected Approach

The installer invokes the installed copy of `scripts/configure_all.py` after a successful standard installation. This reuses the current authority for OAuth scope checks, API verification, account matching, Chat runtime checks, passcode guidance, and owner-only state handling.

The installer does not duplicate configuration-validity rules and does not run the normal digest collector. Installation and configuration remain separate internal components joined by one post-install subprocess boundary.

## Trigger Rules

Post-install configuration is enabled by default when all of the following are true:

- the install is not a dry run;
- the user did not pass a custom `--skills-dir`;
- `TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL` is not false-like;
- the Skill copy or symlink installation completed successfully.

It is skipped when any of the following is true:

- `--dry-run` is active;
- `--skills-dir` targets a custom directory;
- `TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL=0` (or another supported false-like value) is set.

The shell installer converts the environment setting into an explicit installer argument. The Python installer remains deterministic and testable from its parsed arguments.

## User Flow

1. The `curl | sh` installer clones the pinned release and installs the Skill.
2. The installed `.state` directory is restored during an upgrade before configuration starts.
3. The Python installer runs the installed `configure_all.py`.
4. In an interactive Terminal, configuration continues in the same window.
5. In a non-interactive agent shell, `configure_all.py` opens one real macOS Terminal and returns after launching it.
6. The existing unified wizard verifies API credentials and read-only scopes, then checks X Chat for the same account.
7. Valid steps are skipped. Missing steps request input locally and use browser OAuth where required.
8. If X Chat has no passcode yet, the wizard gives the existing friendly X Messages guidance. The Skill remains installed.

The installer never asks for secrets in Agent chat and never starts data collection.

## Failure Handling

Installation is committed before post-install configuration begins. A configuration failure does not remove the installed Skill, discard restored state, or roll back to a backup.

If the configuration subprocess exits unsuccessfully, the installer exits unsuccessfully with a short actionable message and the exact installed-client configuration command. Python tracebacks from subprocess orchestration are not shown.

When the wizard launches a separate Terminal successfully, that launch counts as successful handoff. The user completes configuration there and later requests the digest normally.

## Command and Documentation Changes

The public Codex and Claude `curl` commands stay structurally unchanged except for the `v1.5.14-beta.14` tag. Automatic configuration is the default.

Users can opt out with:

```bash
curl -fsSL <installer-url> | env TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL=0 ... sh
```

Documentation must distinguish installation-time configuration from first-digest fallback configuration. The normal digest wrapper still detects missing or invalid configuration and can reopen the same wizard later.

## Testing

Automated coverage must prove:

1. standard installs request post-install configuration;
2. `TWITTER_DIGEST_CONFIGURE_AFTER_INSTALL=0` suppresses it;
3. `--skills-dir` suppresses it;
4. dry runs suppress it;
5. the installed copy of `configure_all.py` is invoked, not the source checkout;
6. subprocess failure keeps the installed Skill and returns friendly guidance without a traceback;
7. upgrade state restoration occurs before configuration invocation;
8. version references are pinned to `v1.5.14-beta.14`;
9. the full existing test suite remains green;
10. public installation can be exercised in a temporary directory without opening configuration.

Manual verification must cover standard Codex and Claude installations with existing configuration preserved, plus a clean isolated home directory that proves the configuration handoff is attempted without exposing credentials.

## Non-Goals

- Do not collect or generate a digest during installation.
- Do not add browser or cookie data sources.
- Do not save the X Chat passcode.
- Do not configure custom `--skills-dir` installations automatically.
- Do not roll back a successfully installed Skill when configuration is incomplete.
