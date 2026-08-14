#!/bin/sh
set -eu

REF="${TWITTER_DIGEST_INSTALL_REF:-main}"
CLIENT="${TWITTER_DIGEST_INSTALL_CLIENT:-auto}"
OPEN_TERMINAL="${TWITTER_DIGEST_OPEN_TERMINAL:-auto}"
SOURCE_DIR="${TWITTER_DIGEST_SOURCE_DIR:-}"
XURL_VERSION="${TWITTER_DIGEST_XURL_VERSION:-1.3.2-beta.3}"
XURL_NPM_PACKAGE="@bankofai/xurl@${XURL_VERSION}"
SKILLS_DIR=""
SKIP_CONFIGURE=0
DRY_RUN=0
CONFIGURE_XURL=""

info() {
  printf '==> %s\n' "$1"
}

fail() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

shell_quote() {
  value="$1"
  printf "'%s'" "$(printf '%s' "$value" | sed "s/'/'\\\\''/g")"
}

applescript_quote() {
  value="$1"
  printf '%s' "$value" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

usage() {
  cat <<'EOF'
Usage: install.sh [options]

Installs twitter-digest with the BofAI-patched xurl binary from the pinned
@bankofai/xurl package. This is not the unmodified official xurl. Node.js and
npm are used only during installation; normal runs invoke the bundled binary.
The installer never replaces a global xurl or reads ~/.xurl.

Options:
  --client auto|codex|claude|all  Target client. Default: auto.
  --skills-dir DIR                Install into an explicit skills directory.
  --skip-configure                Skip post-install OAuth and X Chat key setup.
  --dry-run                       Print target actions without changing files.
  -h, --help                      Show this help.

Environment overrides:
  TWITTER_DIGEST_INSTALL_REF      BofAI/skills Git ref. Default: main.
  TWITTER_DIGEST_SOURCE_DIR       Local twitter-digest source directory.
  TWITTER_DIGEST_OPEN_TERMINAL    auto, 1, or 0. Default: auto.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --client)
      [ "$#" -ge 2 ] || fail "--client requires a value"
      CLIENT="$2"
      shift 2
      ;;
    --client=*)
      CLIENT="${1#--client=}"
      shift
      ;;
    --skills-dir)
      [ "$#" -ge 2 ] || fail "--skills-dir requires a value"
      SKILLS_DIR="$2"
      shift 2
      ;;
    --skills-dir=*)
      SKILLS_DIR="${1#--skills-dir=}"
      shift
      ;;
    --skip-configure)
      SKIP_CONFIGURE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

case "$CLIENT" in
  auto|codex|claude|all) ;;
  *) fail "--client must be auto, codex, claude, or all" ;;
esac

[ -n "$XURL_VERSION" ] || fail "TWITTER_DIGEST_XURL_VERSION cannot be empty"
[ "$XURL_VERSION" = "1.3.2-beta.3" ] || fail "This installer is pinned to xurl 1.3.2-beta.3"

running_under_agent() {
  if [ -n "${CODEX_THREAD_ID:-}" ] || [ -n "${CODEX_CI:-}" ] || [ "${__CFBundleIdentifier:-}" = "com.openai.codex" ]; then
    return 0
  fi
  if env | grep -Eq '^(CLAUDE|ANTHROPIC)'; then
    return 0
  fi
  return 1
}

should_open_terminal() {
  if [ "${TWITTER_DIGEST_TERMINAL_CHILD:-}" = "1" ] || [ "$DRY_RUN" = "1" ]; then
    return 1
  fi
  case "$OPEN_TERMINAL" in
    1|true|yes) return 0 ;;
    0|false|no) return 1 ;;
    auto) ;;
    *) fail "TWITTER_DIGEST_OPEN_TERMINAL must be auto, 1, or 0" ;;
  esac
  [ "$(uname -s)" = "Darwin" ] || return 1
  if running_under_agent || [ ! -t 0 ]; then
    return 0
  fi
  return 1
}

open_self_in_terminal_and_exit() {
  command_exists osascript || fail "Cannot open macOS Terminal because osascript is unavailable"
  args_text=""
  args_text="$args_text --client $(shell_quote "$CLIENT")"
  if [ -n "$SKILLS_DIR" ]; then
    args_text="$args_text --skills-dir $(shell_quote "$SKILLS_DIR")"
  fi
  if [ "$SKIP_CONFIGURE" = "1" ]; then
    args_text="$args_text --skip-configure"
  fi

  env_text="TWITTER_DIGEST_TERMINAL_CHILD=1 TWITTER_DIGEST_OPEN_TERMINAL=0 TWITTER_DIGEST_INSTALL_REF=$(shell_quote "$REF") TWITTER_DIGEST_INSTALL_CLIENT=$(shell_quote "$CLIENT") TWITTER_DIGEST_XURL_VERSION=$(shell_quote "$XURL_VERSION")"
  if [ -n "$SOURCE_DIR" ]; then
    installer_path="$SOURCE_DIR/install.sh"
    [ -f "$installer_path" ] || fail "Local installer not found: $installer_path"
    env_text="$env_text TWITTER_DIGEST_SOURCE_DIR=$(shell_quote "$SOURCE_DIR")"
    command_text="cd ~ && env $env_text /bin/sh $(shell_quote "$installer_path")${args_text}; printf '\\nPress Enter to close this window...'; IFS= read -r _"
  else
    command_exists curl || fail "curl is required to open the installer in Terminal"
    installer_url="https://raw.githubusercontent.com/BofAI/skills/${REF}/twitter-digest/install.sh"
    command_text="cd ~ && INSTALL_TMP=\"\$(mktemp -d)\" && INSTALL_SH=\"\$INSTALL_TMP/twitter-digest-install.sh\" && curl -fsSL $(shell_quote "$installer_url") -o \"\$INSTALL_SH\" && chmod 700 \"\$INSTALL_SH\" && env $env_text /bin/sh \"\$INSTALL_SH\"${args_text}; printf '\\nPress Enter to close this window...'; IFS= read -r _"
  fi

  osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$(applescript_quote "$command_text")"
end tell
OSA
  info "Opened Terminal for twitter-digest installation. Continue there."
  exit 0
}

if should_open_terminal; then
  open_self_in_terminal_and_exit
fi

has_operator_tty() {
  [ -r /dev/tty ] && [ -w /dev/tty ] && ( : </dev/tty ) 2>/dev/null
}

prompt_value() {
  label=$1
  default_value=${2:-}
  if [ -n "$default_value" ]; then
    prompt_text="$label [$default_value]: "
  else
    prompt_text="$label: "
  fi

  if has_operator_tty; then
    printf '%s' "$prompt_text" >/dev/tty
    IFS= read -r answer </dev/tty || fail "Input cancelled"
  else
    printf '%s' "$prompt_text" >&2
    IFS= read -r answer || fail "Input cancelled"
  fi

  if [ -z "$answer" ]; then
    answer=$default_value
  fi
  [ -n "$answer" ] || fail "$label is required"
  printf '%s\n' "$answer"
}

prompt_secret() {
  label=$1
  if has_operator_tty && command_exists stty; then
    old_stty="$(stty -g </dev/tty)"
    trap 'stty "$old_stty" </dev/tty 2>/dev/null || true' EXIT HUP INT TERM
    printf '%s: ' "$label" >/dev/tty
    stty -echo </dev/tty
    IFS= read -r answer </dev/tty || {
      stty "$old_stty" </dev/tty
      fail "Input cancelled"
    }
    stty "$old_stty" </dev/tty
    printf '\n' >/dev/tty
    trap - EXIT HUP INT TERM
  else
    printf '%s: ' "$label" >&2
    IFS= read -r answer || fail "Input cancelled"
  fi
  [ -n "$answer" ] || fail "$label is required"
  printf '%s\n' "$answer"
}

configured_apps() {
  xurl_path=$1
  "$xurl_path" auth apps list 2>/dev/null |
    sed -n '/ (client_id:/ {
      s/^  //
      s/^▸ //
      s/ (client_id:.*$//
      p
    }'
}

whoami_username() {
  xurl_path=$1
  app_name=$2
  "$xurl_path" token --app "$app_name" >/dev/null 2>&1 || return 1
  identity_json="$("$xurl_path" whoami --auth oauth2 --app "$app_name" 2>/dev/null)" || return 1
  printf '%s' "$identity_json" | node -e '
    const fs = require("fs");
    try {
      const value = JSON.parse(fs.readFileSync(0, "utf8"));
      const username = value && value.data && value.data.username;
      if (typeof username !== "string" || username.length === 0) process.exit(1);
      process.stdout.write(username);
    } catch (_) {
      process.exit(1);
    }
  '
}

select_or_register_app() {
  xurl_path=$1
  apps_file="$WORKDIR/configured-apps"
  configured_apps "$xurl_path" >"$apps_file"
  app_count="$(sed -n '$=' "$apps_file")"
  app_count=${app_count:-0}

  if [ "$app_count" -eq 1 ]; then
    sed -n '1p' "$apps_file"
    return
  fi

  if [ "$app_count" -gt 1 ]; then
    printf '\nRegistered X Apps:\n' >&2
    item=1
    while IFS= read -r app_name; do
      printf '  %s) %s\n' "$item" "$app_name" >&2
      item=$((item + 1))
    done <"$apps_file"
    selection="$(prompt_value 'Select App number' '1')"
    case "$selection" in
      *[!0-9]*|0) fail "Invalid App selection" ;;
    esac
    selected_app="$(sed -n "${selection}p" "$apps_file")"
    [ -n "$selected_app" ] || fail "Invalid App selection"
    printf '%s\n' "$selected_app"
    return
  fi

  printf '\nNo X App is registered in xurl. Enter the X Developer App credentials.\n' >&2
  app_name="$(prompt_value 'App name' '')"
  client_id="$(prompt_value 'OAuth2 Client ID' '')"
  client_secret="$(prompt_secret 'OAuth2 Client Secret')"
  redirect_uri="$(prompt_value 'Callback / Redirect URI' 'http://localhost:8080/callback')"
  "$xurl_path" auth apps add "$app_name" \
    --client-id "$client_id" \
    --client-secret "$client_secret" \
    --redirect-uri "$redirect_uri" >/dev/null || fail "Could not register X App $app_name"
  printf '%s\n' "$app_name"
}

run_oauth2() {
  xurl_path=$1
  app_name=$2
  if [ "$(uname -s)" != "Darwin" ] && [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    if has_operator_tty; then
      "$xurl_path" auth oauth2 --headless --app "$app_name" </dev/tty
    else
      "$xurl_path" auth oauth2 --headless --app "$app_name"
    fi
  else
    "$xurl_path" auth oauth2 --app "$app_name"
  fi
}

print_chat_key_recovery() {
  xurl_path=$1
  printf 'X Chat keys could not be restored. Enable X Chat in an official X client first, then retry:\n  %s chat keys restore\n' \
    "$(shell_quote "$xurl_path")" >&2
}

print_chat_status_retry() {
  xurl_path=$1
  printf 'X Chat key status could not be verified. Retry in Terminal:\n  %s chat keys status --auth oauth2\n' \
    "$(shell_quote "$xurl_path")" >&2
}

print_unregistered_chat_key() {
  xurl_path=$1
  printf 'The local X Chat key is not registered for this account. Use an official X client to establish the account key, then retry:\n  %s chat keys status --auth oauth2\n' \
    "$(shell_quote "$xurl_path")" >&2
}

chat_keys_ready() {
  keys_status=$1
  case "$keys_status" in
    *"← this machine"*) return 0 ;;
    *) return 1 ;;
  esac
}

local_chat_keys_present() {
  keys_status=$1
  normalized_keys_state="$(printf '%s\n' "$keys_status" | sed -n 's/^[[:space:]]*local keys:[[:space:]]*present.*$/present/p')"
  [ "$normalized_keys_state" = present ]
}

configure_xchat_keys() {
  xurl_path=$1
  if keys_status="$("$xurl_path" chat keys status --auth oauth2 2>/dev/null)"; then
    keys_status_ok=1
  else
    keys_status_ok=0
  fi
  if [ "$keys_status_ok" -ne 1 ]; then
    print_chat_status_retry "$xurl_path"
    return 1
  fi
  if chat_keys_ready "$keys_status"; then
    info "X Chat keys are ready"
    return
  fi
  if local_chat_keys_present "$keys_status"; then
    print_unregistered_chat_key "$xurl_path"
    return 1
  fi

  restore_answer="$(prompt_value 'Restore existing X Chat keys now? (Y/n)' 'y')"
  case "$restore_answer" in
    y|Y|yes|YES|Yes) ;;
    *)
      print_chat_key_recovery "$xurl_path"
      return 1
      ;;
  esac

  if has_operator_tty; then
    if ! "$xurl_path" chat keys restore --auth oauth2 </dev/tty; then
      print_chat_key_recovery "$xurl_path"
      return 1
    fi
  elif ! "$xurl_path" chat keys restore --auth oauth2; then
    print_chat_key_recovery "$xurl_path"
    return 1
  fi

  if keys_status="$("$xurl_path" chat keys status --auth oauth2 2>/dev/null)"; then
    keys_status_ok=1
  else
    keys_status_ok=0
  fi
  if [ "$keys_status_ok" -eq 1 ] && chat_keys_ready "$keys_status"; then
    info "X Chat keys are ready"
    return
  fi
  if [ "$keys_status_ok" -ne 1 ]; then
    print_chat_status_retry "$xurl_path"
  else
    print_chat_key_recovery "$xurl_path"
  fi
  return 1
}

configure_installed_xurl() {
  xurl_path=$1
  if "$xurl_path" token >/dev/null 2>&1 && "$xurl_path" whoami --auth oauth2 >/dev/null 2>&1; then
    info "Existing X OAuth2 authorization is ready"
    configure_xchat_keys "$xurl_path"
    return
  fi

  app_name="$(select_or_register_app "$xurl_path")"
  "$xurl_path" auth default "$app_name" >/dev/null || fail "Could not select X App $app_name"
  username="$(whoami_username "$xurl_path" "$app_name" || true)"
  if [ -n "$username" ]; then
    "$xurl_path" auth default "$app_name" "$username" >/dev/null || fail "Could not select @$username for X App $app_name"
    if "$xurl_path" token >/dev/null 2>&1 && "$xurl_path" whoami --auth oauth2 >/dev/null 2>&1; then
      info "Reused OAuth2 authorization for @$username"
      configure_xchat_keys "$xurl_path"
      return
    fi
  fi

  info "Opening X OAuth2 authorization for App $app_name"
  if ! run_oauth2 "$xurl_path" "$app_name"; then
    printf 'Authorization was not completed. Retry in Terminal:\n  %s auth oauth2 --app %s\n' \
      "$(shell_quote "$xurl_path")" "$(shell_quote "$app_name")" >&2
    return 1
  fi

  username="$(whoami_username "$xurl_path" "$app_name" || true)"
  [ -n "$username" ] || fail "OAuth2 completed but xurl did not report an authorized username"
  "$xurl_path" auth default "$app_name" "$username" >/dev/null || fail "Could not set the default X account"
  "$xurl_path" token >/dev/null 2>&1 || fail "OAuth2 token verification failed for @$username"
  "$xurl_path" whoami --auth oauth2 >/dev/null 2>&1 || fail "OAuth2 identity verification failed for @$username"
  info "Authorized X account @$username"
  configure_xchat_keys "$xurl_path"
}

detect_client() {
  if [ -n "${CODEX_THREAD_ID:-}" ] || [ "${__CFBundleIdentifier:-}" = "com.openai.codex" ]; then
    printf 'codex'
    return
  fi
  if env | grep -Eq '^(CLAUDE|ANTHROPIC)'; then
    printf 'claude'
    return
  fi
  if [ -d "$HOME/.codex/skills" ] && [ ! -d "$HOME/.claude/skills" ]; then
    printf 'codex'
    return
  fi
  if [ -d "$HOME/.claude/skills" ] && [ ! -d "$HOME/.codex/skills" ]; then
    printf 'claude'
    return
  fi
  printf 'codex'
}

if [ -z "$SKILLS_DIR" ] && [ "$CLIENT" = "auto" ]; then
  CLIENT="$(detect_client)"
fi

if [ "$DRY_RUN" = "1" ]; then
  if [ -n "$SKILLS_DIR" ]; then
    info "Would install twitter-digest and bundled $XURL_NPM_PACKAGE into $SKILLS_DIR/twitter-digest"
  else
    case "$CLIENT" in
      codex) info "Would install twitter-digest and bundled $XURL_NPM_PACKAGE into $HOME/.codex/skills/twitter-digest" ;;
      claude) info "Would install twitter-digest and bundled $XURL_NPM_PACKAGE into $HOME/.claude/skills/twitter-digest" ;;
      all)
        info "Would install twitter-digest and bundled $XURL_NPM_PACKAGE into $HOME/.codex/skills/twitter-digest"
        info "Would install twitter-digest and bundled $XURL_NPM_PACKAGE into $HOME/.claude/skills/twitter-digest"
        ;;
    esac
  fi
  exit 0
fi

case "$(uname -s)/$(uname -m)" in
  Darwin/arm64|Darwin/x86_64|Linux/x86_64|Linux/amd64) ;;
  *) fail "twitter-digest requires full X Chat support: macOS arm64/amd64 or Linux amd64" ;;
esac

for required_command in mktemp tar sed cp mv mkdir chmod date node npm; do
  command_exists "$required_command" || fail "$required_command is required"
done

WORKDIR="$(mktemp -d 2>/dev/null || mktemp -d -t twitter-digest)"
PACKAGE_DIR="$WORKDIR/twitter-digest"
mkdir -p "$PACKAGE_DIR/agents" "$PACKAGE_DIR/bin"

copy_source_file() {
  relative_path="$1"
  destination="$PACKAGE_DIR/$relative_path"
  if [ -n "$SOURCE_DIR" ]; then
    source_path="$SOURCE_DIR/$relative_path"
    [ -f "$source_path" ] || fail "Missing source file: $source_path"
    cp "$source_path" "$destination"
  else
    command_exists curl || fail "curl is required for a remote install"
    source_url="https://raw.githubusercontent.com/BofAI/skills/${REF}/twitter-digest/${relative_path}"
    curl -fsSL "$source_url" -o "$destination" || fail "Could not download $relative_path"
  fi
}

copy_source_file "SKILL.md"
copy_source_file "agents/openai.yaml"
copy_source_file "install.sh"
copy_source_file "uninstall.sh"

XURL_NPM_ROOT="$WORKDIR/xurl-npm"
mkdir -p "$XURL_NPM_ROOT"
info "Installing $XURL_NPM_PACKAGE from npm"
npm install \
  --prefix "$XURL_NPM_ROOT" \
  --no-save \
  --omit=dev \
  --prefer-online \
  "$XURL_NPM_PACKAGE" || fail "Could not install $XURL_NPM_PACKAGE from npm"

XURL_NPM_PACKAGE_DIR="$XURL_NPM_ROOT/node_modules/@bankofai/xurl"
XURL_NPM_MANIFEST="$XURL_NPM_PACKAGE_DIR/package.json"
[ -f "$XURL_NPM_MANIFEST" ] || fail "$XURL_NPM_PACKAGE did not install the expected package manifest"
installed_package_name="$(node -e 'process.stdout.write(require(process.argv[1]).name || "")' "$XURL_NPM_MANIFEST")"
installed_package_version="$(node -e 'process.stdout.write(require(process.argv[1]).version || "")' "$XURL_NPM_MANIFEST")"
[ "$installed_package_name" = "@bankofai/xurl" ] || fail "Installed npm package identity is not @bankofai/xurl"
[ "$installed_package_version" = "$XURL_VERSION" ] || fail "Installed @bankofai/xurl version is not $XURL_VERSION"

XURL_NPM_BINARY="$XURL_NPM_PACKAGE_DIR/binary/xurl"
[ -f "$XURL_NPM_BINARY" ] || fail "$XURL_NPM_PACKAGE did not install the expected BofAI-patched binary"
cp "$XURL_NPM_BINARY" "$PACKAGE_DIR/bin/xurl"
chmod 755 "$PACKAGE_DIR/bin/xurl" "$PACKAGE_DIR/install.sh" "$PACKAGE_DIR/uninstall.sh"

version_output="$($PACKAGE_DIR/bin/xurl version 2>/dev/null || true)"
[ "$version_output" = "xurl $XURL_VERSION" ] || fail "Bundled binary version check failed"
chat_help="$($PACKAGE_DIR/bin/xurl chat --help 2>&1 || true)"
case "$chat_help" in
  *"not available in this build"*) fail "$XURL_NPM_PACKAGE does not include X Chat on this platform" ;;
esac

install_target() {
  skills_root="$1"
  target="$skills_root/twitter-digest"
  stamp="$(date +%Y%m%d-%H%M%S)"
  staging="$skills_root/.twitter-digest-install-$stamp-$$"

  mkdir -p "$skills_root"
  cp -R "$PACKAGE_DIR" "$staging"

  if [ -e "$target" ] || [ -L "$target" ]; then
    backup_root="$skills_root/.backups"
    backup="$backup_root/twitter-digest-$stamp"
    suffix=1
    while [ -e "$backup" ] || [ -L "$backup" ]; do
      suffix=$((suffix + 1))
      backup="$backup_root/twitter-digest-$stamp-$suffix"
    done
    mkdir -p "$backup_root"
    mv "$target" "$backup"
    if [ -f "$backup/SKILL.md" ]; then
      mv "$backup/SKILL.md" "$backup/SKILL.md.disabled"
    fi
    info "Preserved the previous installation at $backup"
  fi

  mv "$staging" "$target"
  if [ -z "$CONFIGURE_XURL" ]; then
    CONFIGURE_XURL="$target/bin/xurl"
  fi
  info "Installed twitter-digest at $target"
  info "Bundled $($target/bin/xurl version)"
  info "Acquired from $XURL_NPM_PACKAGE"
}

if [ -n "$SKILLS_DIR" ]; then
  install_target "$SKILLS_DIR"
else
  case "$CLIENT" in
    codex) install_target "$HOME/.codex/skills" ;;
    claude) install_target "$HOME/.claude/skills" ;;
    all)
      install_target "$HOME/.codex/skills"
      install_target "$HOME/.claude/skills"
      ;;
  esac
fi

if [ "$SKIP_CONFIGURE" = "0" ]; then
  configure_installed_xurl "$CONFIGURE_XURL"
fi

printf '\nExisting xurl authorization and Chat keys in ~/.xurl were preserved.\n'
