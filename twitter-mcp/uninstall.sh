#!/bin/sh
set -eu

CLIENT="${X_MCP_UNINSTALL_CLIENT:-auto}"
PURGE_STATE="${X_MCP_PURGE_STATE:-0}"
REMOVE_MCP_CONFIG="${X_MCP_REMOVE_MCP_CONFIG:-0}"
UNINSTALL_XURL="${X_MCP_UNINSTALL_XURL:-0}"
SERVER_NAME="${X_MCP_SERVER_NAME:-xapi}"
DRY_RUN=0

info() {
  printf '==> %s\n' "$1"
}

fail() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

truthy() {
  case "${1:-}" in
    1|true|yes) return 0 ;;
    *) return 1 ;;
  esac
}

usage() {
  cat <<'EOF'
Usage: uninstall.sh [--client auto|codex|claude|all] [--purge-state] [--remove-mcp-config] [--uninstall-xurl] [--dry-run]

Default uninstall moves installed twitter-mcp skill directories to .backups/
and disables SKILL.md, preserving .state in the backup. xurl, OAuth app config,
and MCP registrations are left in place unless explicitly removed.

Options:
  --client             Target client. Default: auto.
  --purge-state        Permanently remove the installed skill directory, including .state.
  --remove-mcp-config  Remove the xapi MCP server registration from Codex/Claude config.
  --uninstall-xurl     Run npm uninstall -g @xdevplatform/xurl.
  --dry-run            Print actions without changing files.
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
    --purge-state)
      PURGE_STATE=1
      shift
      ;;
    --remove-mcp-config)
      REMOVE_MCP_CONFIG=1
      shift
      ;;
    --uninstall-xurl)
      UNINSTALL_XURL=1
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

detect_client() {
  if env | grep -q '^CODEX_'; then
    printf 'codex'
    return
  fi
  if env | grep -q '^CLAUDE'; then
    printf 'claude'
    return
  fi
  if [ -d "$HOME/.codex/skills/twitter-mcp" ] && [ ! -d "$HOME/.claude/skills/twitter-mcp" ]; then
    printf 'codex'
    return
  fi
  if [ -d "$HOME/.claude/skills/twitter-mcp" ] && [ ! -d "$HOME/.codex/skills/twitter-mcp" ]; then
    printf 'claude'
    return
  fi
  printf 'all'
}

backup_target() {
  skills_dir="$1"
  target="$skills_dir/twitter-mcp"
  if [ ! -e "$target" ] && [ ! -L "$target" ]; then
    info "twitter-mcp is not installed at $target"
    return 0
  fi

  if truthy "$PURGE_STATE"; then
    if [ "$DRY_RUN" = "1" ]; then
      info "Would permanently remove $target"
    else
      rm -rf "$target"
      info "Removed $target"
    fi
    return 0
  fi

  backup_dir="$skills_dir/.backups"
  stamp="$(date +%Y%m%d-%H%M%S)"
  backup="$backup_dir/twitter-mcp-uninstalled-$stamp"
  suffix=1
  while [ -e "$backup" ] || [ -L "$backup" ]; do
    suffix=$((suffix + 1))
    backup="$backup_dir/twitter-mcp-uninstalled-$stamp-$suffix"
  done

  if [ "$DRY_RUN" = "1" ]; then
    info "Would move $target to $backup"
    return 0
  fi

  mkdir -p "$backup_dir"
  mv "$target" "$backup"
  if [ -f "$backup/SKILL.md" ]; then
    mv "$backup/SKILL.md" "$backup/SKILL.md.disabled"
  fi
  info "Uninstalled twitter-mcp from $target"
  info "Preserved previous install and .state at $backup"
}

remove_codex_mcp_config() {
  config_path="${CODEX_CONFIG:-$HOME/.codex/config.toml}"
  if [ ! -f "$config_path" ]; then
    info "Codex config not found at $config_path"
    return 0
  fi
  if [ "$DRY_RUN" = "1" ]; then
    info "Would remove [mcp_servers.$SERVER_NAME] from $config_path"
    return 0
  fi
  tmp_config="${config_path}.tmp.$$"
  marker="[mcp_servers.${SERVER_NAME}]"
  subtable_prefix="[mcp_servers.${SERVER_NAME}."
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
  info "Removed Codex MCP server '$SERVER_NAME' from $config_path"
}

remove_claude_mcp_config() {
  if ! command -v claude >/dev/null 2>&1; then
    info "Claude Code CLI not found; skipped Claude MCP removal."
    return 0
  fi
  if [ "$DRY_RUN" = "1" ]; then
    info "Would run: claude mcp remove $SERVER_NAME"
    return 0
  fi
  if claude mcp get "$SERVER_NAME" >/dev/null 2>&1; then
    claude mcp remove "$SERVER_NAME"
    info "Removed Claude MCP server '$SERVER_NAME'"
  else
    info "Claude MCP server '$SERVER_NAME' was not registered."
  fi
}

remove_xurl() {
  if ! truthy "$UNINSTALL_XURL"; then
    return 0
  fi
  if [ "$DRY_RUN" = "1" ]; then
    info "Would run: npm uninstall -g @xdevplatform/xurl"
    return 0
  fi
  if ! command -v npm >/dev/null 2>&1; then
    info "npm not found; skipped xurl uninstall."
    return 0
  fi
  npm uninstall -g @xdevplatform/xurl
}

targets="$CLIENT"
if [ "$CLIENT" = "auto" ]; then
  targets="$(detect_client)"
fi

case "$targets" in
  codex)
    backup_target "$HOME/.codex/skills"
    if truthy "$REMOVE_MCP_CONFIG"; then remove_codex_mcp_config; fi
    ;;
  claude)
    backup_target "$HOME/.claude/skills"
    if truthy "$REMOVE_MCP_CONFIG"; then remove_claude_mcp_config; fi
    ;;
  all)
    backup_target "$HOME/.codex/skills"
    backup_target "$HOME/.claude/skills"
    if truthy "$REMOVE_MCP_CONFIG"; then
      remove_codex_mcp_config
      remove_claude_mcp_config
    fi
    ;;
esac

remove_xurl
