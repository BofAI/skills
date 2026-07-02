#!/bin/sh
set -eu

TAG="${X_MCP_INSTALL_TAG:-v1.5.12-beta.9}"
BASE_URL="${X_MCP_INSTALL_BASE_URL:-https://raw.githubusercontent.com/BofAI/skills/${TAG}/twitter-mcp}"
REGISTER_CODEX="${X_MCP_REGISTER_CODEX:-1}"
REGISTER_CLAUDE="${X_MCP_REGISTER_CLAUDE:-auto}"
REGISTER_CODEX_MCP="${X_MCP_REGISTER_CODEX_MCP:-0}"
REGISTER_CLAUDE_MCP="${X_MCP_REGISTER_CLAUDE_MCP:-0}"
OPEN_TERMINAL="${X_MCP_OPEN_TERMINAL:-auto}"
APP_NAME="${X_MCP_APP_NAME:-xmcp}"
APP_NAME_EXPLICIT="${X_MCP_APP_NAME+x}"

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

truthy() {
  case "${1:-}" in
    1|true|yes) return 0 ;;
    *) return 1 ;;
  esac
}

running_under_agent() {
  if [ -n "${CODEX_THREAD_ID:-}" ] || [ -n "${CODEX_CI:-}" ] || [ "${__CFBundleIdentifier:-}" = "com.openai.codex" ]; then
    return 0
  fi
  if env | grep -Eq '^(CLAUDE|ANTHROPIC)'; then
    return 0
  fi
  return 1
}

xurl_app_exists() {
  if ! command_exists xurl; then
    return 1
  fi
  xurl auth apps list 2>/dev/null | sed -n 's/^▸ \([^ ]*\).*/\1/p' | grep -Fx "$APP_NAME" >/dev/null 2>&1
}

infer_app_name_if_needed() {
  if [ -n "$APP_NAME_EXPLICIT" ] || ! command_exists xurl; then
    return 0
  fi
  apps="$(xurl auth apps list 2>/dev/null | sed -n 's/^▸ \([^ ]*\).*/\1/p' | sort -u || true)"
  app_count="$(printf '%s\n' "$apps" | sed '/^$/d' | wc -l | tr -d ' ')"
  if [ "$app_count" = "1" ]; then
    APP_NAME="$(printf '%s\n' "$apps" | sed -n '/^$/!{p;q;}')"
    info "Using existing xurl app '${APP_NAME}'. Set X_MCP_APP_NAME to override."
  fi
}

xurl_oauth_ready() {
  if [ "${X_MCP_FORCE_CONFIGURE:-0}" = "1" ] || [ "${X_MCP_FORCE_CONFIGURE:-}" = "true" ]; then
    return 1
  fi
  if ! xurl_app_exists; then
    return 1
  fi
  xurl token --app "$APP_NAME" >/dev/null 2>&1
}

should_open_terminal() {
  if [ "${X_MCP_TERMINAL_CHILD:-}" = "1" ]; then
    return 1
  fi
  if xurl_oauth_ready; then
    return 1
  fi
  case "$OPEN_TERMINAL" in
    1|true|yes) return 0 ;;
    0|false|no) return 1 ;;
  esac
  if [ "$(uname -s)" != "Darwin" ]; then
    return 1
  fi
  if running_under_agent; then
    return 0
  fi
  if [ ! -t 0 ]; then
    return 0
  fi
  return 1
}

open_self_in_terminal_and_exit() {
  command_exists osascript || fail "Cannot open macOS Terminal because osascript is unavailable."
  command_exists curl || fail "curl is required to open the installer in Terminal."

  installer_url="${BASE_URL%/}/install.sh"
  args_text=""
  for arg in "$@"; do
    args_text="${args_text} $(shell_quote "$arg")"
  done
  command_text="cd ~ && TMPDIR=\"\$(mktemp -d)\" && INSTALL_SH=\"\$TMPDIR/twitter-mcp-install.sh\" && curl -fsSL $(shell_quote "$installer_url") -o \"\$INSTALL_SH\" && chmod 700 \"\$INSTALL_SH\" && env X_MCP_TERMINAL_CHILD=1 X_MCP_OPEN_TERMINAL=0 X_MCP_INSTALL_TAG=$(shell_quote "$TAG") X_MCP_INSTALL_BASE_URL=$(shell_quote "$BASE_URL") X_MCP_REGISTER_CODEX=$(shell_quote "$REGISTER_CODEX") X_MCP_REGISTER_CLAUDE=$(shell_quote "$REGISTER_CLAUDE") X_MCP_REGISTER_CODEX_MCP=$(shell_quote "$REGISTER_CODEX_MCP") X_MCP_REGISTER_CLAUDE_MCP=$(shell_quote "$REGISTER_CLAUDE_MCP") X_MCP_APP_NAME=$(shell_quote "$APP_NAME") X_MCP_FORCE_CONFIGURE=$(shell_quote "${X_MCP_FORCE_CONFIGURE:-0}") /bin/sh \"\$INSTALL_SH\"${args_text}; printf '\\nPress Enter to close this window...'; IFS= read -r _"
  osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$(applescript_quote "$command_text")"
end tell
OSA
  info "Opened Terminal for twitter-mcp installation. Continue there."
  exit 0
}

infer_app_name_if_needed

if should_open_terminal; then
  open_self_in_terminal_and_exit "$@"
fi

if command -v mktemp >/dev/null 2>&1; then
  WORKDIR="$(mktemp -d 2>/dev/null || mktemp -d -t twitter-mcp)"
else
  WORKDIR="${TMPDIR:-/tmp}/twitter-mcp-install.$$"
  mkdir -p "$WORKDIR"
fi

INSTALLER="$WORKDIR/install_xmcp.sh"
INSTALLER_URL="${BASE_URL%/}/scripts/install_xmcp.sh"

download_file() {
  url="$1"
  output="$2"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" -o "$output"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$output" "$url"
  else
    printf 'Error: curl or wget is required to download %s\n' "$url" >&2
    exit 1
  fi
}

RESTORED_BACKUP=""

should_install_claude_skill() {
  if truthy "$REGISTER_CLAUDE"; then
    return 0
  fi
  if [ "$REGISTER_CLAUDE" = "auto" ] && command -v claude >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

backup_existing_skill() {
  target="$1"
  skills_dir="$2"
  RESTORED_BACKUP=""
  if [ ! -e "$target" ] && [ ! -L "$target" ]; then
    return 0
  fi
  backup_dir="$skills_dir/.backups"
  stamp="$(date +%Y%m%d-%H%M%S)"
  backup="$backup_dir/twitter-mcp-$stamp"
  suffix=1
  while [ -e "$backup" ] || [ -L "$backup" ]; do
    suffix=$((suffix + 1))
    backup="$backup_dir/twitter-mcp-$stamp-$suffix"
  done
  mkdir -p "$backup_dir"
  mv "$target" "$backup"
  if [ -f "$backup/SKILL.md" ]; then
    mv "$backup/SKILL.md" "$backup/SKILL.md.disabled"
  fi
  RESTORED_BACKUP="$backup"
  info "Existing twitter-mcp skill moved to $backup"
}

restore_state_from_backup() {
  backup="$1"
  target="$2"
  if [ -z "$backup" ]; then
    return 0
  fi
  if [ ! -d "$backup/.state" ]; then
    return 0
  fi
  if [ -e "$target/.state" ] || [ -L "$target/.state" ]; then
    return 0
  fi
  cp -R "$backup/.state" "$target/.state"
  info "Preserved existing state: $target/.state"
}

install_skill_copy() {
  skills_dir="$1"
  target="$skills_dir/twitter-mcp"
  staging="$WORKDIR/twitter-mcp-skill"
  rm -rf "$staging"
  mkdir -p "$staging/scripts" "$staging/agents"
  download_file "${BASE_URL%/}/SKILL.md" "$staging/SKILL.md"
  download_file "${BASE_URL%/}/install.sh" "$staging/install.sh"
  download_file "${BASE_URL%/}/uninstall.sh" "$staging/uninstall.sh"
  download_file "${BASE_URL%/}/agents/openai.yaml" "$staging/agents/openai.yaml"
  download_file "${BASE_URL%/}/scripts/install_xmcp.sh" "$staging/scripts/install_xmcp.sh"
  chmod 700 "$staging/install.sh" "$staging/uninstall.sh" "$staging/scripts/install_xmcp.sh"
  mkdir -p "$skills_dir"
  backup_existing_skill "$target" "$skills_dir"
  mv "$staging" "$target"
  restore_state_from_backup "$RESTORED_BACKUP" "$target"
  info "Installed twitter-mcp skill to $target"
}

if truthy "$REGISTER_CODEX"; then
  install_skill_copy "$HOME/.codex/skills"
fi

if should_install_claude_skill; then
  install_skill_copy "$HOME/.claude/skills"
fi

download_file "$INSTALLER_URL" "$INSTALLER"

chmod 700 "$INSTALLER"
X_MCP_REGISTER_CODEX="$REGISTER_CODEX_MCP" X_MCP_REGISTER_CLAUDE="$REGISTER_CLAUDE_MCP" X_MCP_APP_NAME="$APP_NAME" X_MCP_FORCE_CONFIGURE="${X_MCP_FORCE_CONFIGURE:-0}" exec /bin/bash "$INSTALLER" "$@"
