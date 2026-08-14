# Twitter Digest First-Install Authorization Design

## Goal

Make the Codex and Claude installers complete first-time X authorization interactively while guaranteeing that the installed executable comes from the pinned BofAI npm package.

## Package contract

- Install exactly `@bankofai/xurl@1.3.2-beta.3` with no fallback to `@xdevplatform/xurl` or a global executable.
- Verify the installed npm package name and version, the bundled executable version, and X Chat availability before replacing an existing skill installation.
- Preserve `~/.xurl` across installation, reinstallation, and uninstall.

## Authorization flow

Unless `--skip-configure` is supplied, run configuration after installing the selected client target.

1. Ask the installed BofAI xurl for registered apps and OAuth status.
2. If a valid OAuth2 user is already selected, reuse it without opening a browser.
3. If registered apps exist but none has OAuth2 credentials:
   - use the only configured app automatically;
   - when several configured apps exist, prompt the operator to select one.
4. If no configured app exists, prompt in the real Terminal for app name, Client ID, Client Secret, and redirect URI. Do not echo the Client Secret. Register the app with the installed BofAI xurl.
5. Run `auth oauth2 --app <app>` so xurl opens the browser and handles the local callback.
6. Determine the authorized username from xurl, set the selected app and user as default, and verify `whoami` succeeds.
7. Check X Chat keys. If local keys are present and registered, finish. Otherwise offer xurl's restore flow in the same Terminal; PIN input remains owned by xurl and is not echoed by the installer. Because xurl cannot create or register a new X Chat key, an account with no existing key must first enable X Chat in an official X client.

## Runtime and failure behavior

- Automatic browser authorization is interactive and therefore runs only in a real Terminal. The existing macOS terminal handoff remains in place when installation starts under Codex, Claude, or piped stdin.
- Linux and headless users receive xurl's `--headless` authorization path when a browser callback cannot be used.
- Cancellation or authorization failure stops configuration with a concise recovery command while leaving the successfully installed skill intact.
- `--skip-configure` remains available for managed or repeatable deployments.

## Verification

- Shell tests cover: BofAI package provenance checks, already-authorized reuse, one-app automatic OAuth, multi-app selection, no-app credential prompts, `--skip-configure`, and failed OAuth.
- Dry-run remains non-mutating.
- Validate the skill metadata and shell syntax, then run clean Codex and Claude installation simulations with isolated temporary homes.
