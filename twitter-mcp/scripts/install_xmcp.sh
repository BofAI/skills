#!/usr/bin/env bash
set -euo pipefail

PACKAGE="${XMCP_PACKAGE:-@xdevplatform/xurl}"
VERSION="${XMCP_VERSION:-latest}"
INSTALL_SPEC="${PACKAGE}@${VERSION}"
APP_NAME="${X_MCP_APP_NAME:-xmcp}"
REDIRECT_URI="${X_MCP_REDIRECT_URI:-http://localhost:8080/callback}"
SERVER_NAME="${X_MCP_SERVER_NAME:-xapi}"
REGISTER_CODEX="${X_MCP_REGISTER_CODEX:-1}"
REGISTER_CLAUDE="${X_MCP_REGISTER_CLAUDE:-auto}"
CODEX_CONFIG="${CODEX_CONFIG:-$HOME/.codex/config.toml}"
OPEN_TERMINAL="${X_MCP_OPEN_TERMINAL:-auto}"
XURL_COMMAND="${X_MCP_XURL_COMMAND:-}"

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
  local value="$1"
  printf "'%s'" "$(printf '%s' "$value" | sed "s/'/'\\\\''/g")"
}

applescript_quote() {
  local value="$1"
  printf '%s' "$value" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

toml_quote() {
  local value="$1"
  printf '"%s"' "$(printf '%s' "$value" | sed 's/\\/\\\\/g; s/"/\\"/g')"
}

resolve_command_path() {
  local command_name="$1"
  local resolved=""
  resolved="$(command -v "$command_name" 2>/dev/null || true)"
  if [ -z "$resolved" ]; then
    return 1
  fi
  case "$resolved" in
    /*) printf '%s' "$resolved" ;;
    *) printf '%s/%s' "$(cd -P "$(dirname "$resolved")" >/dev/null 2>&1 && pwd)" "$(basename "$resolved")" ;;
  esac
}

script_path() {
  local source="${BASH_SOURCE[0]}"
  local dir=""
  while [ -L "$source" ]; do
    dir="$(cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd)"
    source="$(readlink "$source")"
    case "$source" in
      /*) ;;
      *) source="$dir/$source" ;;
    esac
  done
  dir="$(cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd)"
  printf '%s/%s' "$dir" "$(basename "$source")"
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

should_open_terminal() {
  if [ "${X_MCP_TERMINAL_CHILD:-}" = "1" ]; then
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

open_in_terminal_and_exit() {
  if ! command_exists osascript; then
    fail "Cannot open macOS Terminal because osascript is unavailable."
  fi
  local path
  path="$(script_path)"
  local cwd
  cwd="$(pwd)"
  local command_text
  command_text="cd $(shell_quote "$cwd") && X_MCP_TERMINAL_CHILD=1 /bin/bash $(shell_quote "$path"); printf '\\nPress Enter to close this window...'; IFS= read -r _"
  osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$(applescript_quote "$command_text")"
end tell
OSA
  info "Opened Terminal for X MCP OAuth2 setup. Continue there."
  exit 0
}

prompt() {
  local name="$1"
  local default_value="${2:-}"
  local value=""
  if [ -n "$default_value" ]; then
    printf '%s [%s]: ' "$name" "$default_value" >&2
  else
    printf '%s: ' "$name" >&2
  fi
  IFS= read -r value
  printf '%s' "${value:-$default_value}"
}

prompt_secret() {
  local name="$1"
  local value=""
  printf '%s: ' "$name" >&2
  if [ -t 0 ]; then
    stty -echo
    IFS= read -r value
    stty echo
    printf '\n' >&2
  else
    IFS= read -r value
  fi
  printf '%s' "$value"
}

register_codex() {
  local config_path="$1"
  local server_name="$2"
  local app_name="$3"
  local xurl_command="$4"
  local marker="[mcp_servers.${server_name}]"
  local subtable_prefix="[mcp_servers.${server_name}."
  local tmp_config=""

  mkdir -p "$(dirname "$config_path")"
  touch "$config_path"
  tmp_config="${config_path}.tmp.$$"

  awk -v marker="$marker" -v subtable_prefix="$subtable_prefix" '
    /^\[/ {
      if ($0 == marker || index($0, subtable_prefix) == 1) {
        skip = 1
        next
      }
      skip = 0
    }
    skip { next }
    { print }
  ' "$config_path" > "$tmp_config"
  mv "$tmp_config" "$config_path"

  {
    printf '\n[mcp_servers.%s]\n' "$server_name"
    printf 'command = %s\n' "$(toml_quote "$xurl_command")"
    printf 'args = [%s, %s, %s, %s]\n' \
      "$(toml_quote '--app')" \
      "$(toml_quote "$app_name")" \
      "$(toml_quote 'mcp')" \
      "$(toml_quote 'https://api.x.com/mcp')"
  } >> "$config_path"

  info "Registered Codex MCP server '${server_name}' in ${config_path} with ${xurl_command}"
}

register_claude() {
  local server_name="$1"
  local app_name="$2"
  local xurl_command="$3"

  if ! command_exists claude; then
    info "Claude Code CLI not found; skipped Claude MCP registration."
    return
  fi

  if claude mcp get "$server_name" >/dev/null 2>&1; then
    info "Claude MCP server '${server_name}' already exists; leaving it unchanged."
    return
  fi

  info "Registering Claude Code MCP server '${server_name}'"
  claude mcp add "$server_name" -- "$xurl_command" --app "$app_name" mcp https://api.x.com/mcp
}

if should_open_terminal; then
  open_in_terminal_and_exit
fi

if ! command_exists node; then
  fail "Node.js is required before installing X MCP. Install Node.js, then rerun this script."
fi

if ! command_exists npm; then
  fail "npm is required before installing X MCP. Install npm, then rerun this script."
fi

info "Installing ${INSTALL_SPEC}"
npm install -g "${INSTALL_SPEC}"

if [ -z "$XURL_COMMAND" ]; then
  XURL_COMMAND="$(resolve_command_path xurl || true)"
fi

if [ -z "$XURL_COMMAND" ] || [ ! -x "$XURL_COMMAND" ]; then
  fail "xurl was installed by npm, but the xurl command is not on PATH."
fi

info "Installed $("$XURL_COMMAND" --version 2>/dev/null || printf 'xurl') at ${XURL_COMMAND}"

CLIENT_ID="${X_MCP_CLIENT_ID:-${X_OAUTH_CLIENT_ID:-}}"
CLIENT_SECRET="${X_MCP_CLIENT_SECRET:-${X_OAUTH_CLIENT_SECRET:-}}"

if [ -z "$CLIENT_ID" ]; then
  if [ ! -t 0 ]; then
    fail "X_MCP_CLIENT_ID is required when stdin is not interactive."
  fi
  CLIENT_ID="$(prompt 'X OAuth Client ID')"
fi

if [ -z "$CLIENT_ID" ]; then
  fail "X OAuth Client ID is required."
fi

if [ -z "${X_MCP_CLIENT_SECRET+x}" ] && [ -z "${X_OAUTH_CLIENT_SECRET+x}" ] && [ -t 0 ]; then
  CLIENT_SECRET="$(prompt_secret 'X OAuth Client Secret (leave empty for public PKCE apps)')"
fi

if [ -t 0 ]; then
  APP_NAME="$(prompt 'xurl app name' "$APP_NAME")"
  REDIRECT_URI="$(prompt 'OAuth callback URL' "$REDIRECT_URI")"
fi

info "Registering xurl OAuth app '${APP_NAME}'"
app_cmd=("$XURL_COMMAND" auth apps add "$APP_NAME" --client-id "$CLIENT_ID" --redirect-uri "$REDIRECT_URI")
if [ -n "$CLIENT_SECRET" ]; then
  app_cmd+=(--client-secret "$CLIENT_SECRET")
fi
"${app_cmd[@]}"

info "Opening X OAuth authorization flow"
"$XURL_COMMAND" auth oauth2 --app "$APP_NAME"

info "Setting '${APP_NAME}' as the default xurl auth app"
"$XURL_COMMAND" auth default "$APP_NAME"

if [ "$REGISTER_CODEX" = "1" ] || [ "$REGISTER_CODEX" = "true" ]; then
  register_codex "$CODEX_CONFIG" "$SERVER_NAME" "$APP_NAME" "$XURL_COMMAND"
else
  info "Skipped Codex MCP registration."
fi

if [ "$REGISTER_CLAUDE" = "1" ] || [ "$REGISTER_CLAUDE" = "true" ]; then
  register_claude "$SERVER_NAME" "$APP_NAME" "$XURL_COMMAND"
elif [ "$REGISTER_CLAUDE" = "auto" ]; then
  if command_exists claude; then
    register_claude "$SERVER_NAME" "$APP_NAME" "$XURL_COMMAND"
  else
    info "Claude Code CLI not found; skipped Claude MCP registration."
  fi
else
  info "Skipped Claude Code MCP registration."
fi

info "Done"
printf '\nX MCP command for MCP clients:\n'
printf '  %s --app %s mcp https://api.x.com/mcp\n' "$XURL_COMMAND" "$APP_NAME"
printf '\nCodex config example:\n'
printf '[mcp_servers.%s]\n' "$SERVER_NAME"
printf 'command = "%s"\n' "$XURL_COMMAND"
printf 'args = ["--app", "%s", "mcp", "https://api.x.com/mcp"]\n' "$APP_NAME"
