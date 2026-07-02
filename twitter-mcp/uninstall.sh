#!/bin/sh
set -eu

CLIENT="${X_MCP_UNINSTALL_CLIENT:-auto}"
PURGE_STATE="${X_MCP_PURGE_STATE:-0}"
REMOVE_MCP_CONFIG="${X_MCP_REMOVE_MCP_CONFIG:-1}"
REMOVE_XURL_APP="${X_MCP_REMOVE_XURL_APP:-1}"
UNINSTALL_XURL="${X_MCP_UNINSTALL_XURL:-1}"
REMOVE_XURL_CONFIG="${X_MCP_REMOVE_XURL_CONFIG:-auto}"
SERVER_NAME="${X_MCP_SERVER_NAME:-xapi}"
APP_NAME="${X_MCP_APP_NAME:-xmcp}"
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
Usage: uninstall.sh [--client auto|codex|claude|all] [--purge-state] [--keep-mcp-config] [--keep-xurl-app] [--keep-xurl] [--keep-xurl-config] [--dry-run]

Default uninstall moves installed twitter-mcp skill directories to .backups/
and disables SKILL.md, preserving .state in the backup. With --purge-state,
the active install and existing twitter-mcp backups are permanently removed.
Uninstall also removes the matching xapi MCP registration and the xmcp xurl
OAuth app/tokens created by the installer, then uninstalls the global
@xdevplatform/xurl package. With --purge-state, it also removes ~/.xurl so
custom-named xurl apps and tokens cannot be reused after reinstall.

Options:
  --client             Target client. Default: auto.
  --purge-state        Permanently remove the installed skill directory, .state, and matching backups.
  --keep-mcp-config    Keep the xapi MCP server registration.
  --remove-mcp-config  Remove the xapi MCP server registration (default).
  --keep-xurl-app      Keep the xmcp xurl app and tokens.
  --remove-xurl-app    Remove the xmcp xurl app and tokens (default).
  --keep-xurl          Keep the global @xdevplatform/xurl package.
  --uninstall-xurl     Run npm uninstall -g @xdevplatform/xurl (default).
  --keep-xurl-config   Keep ~/.xurl even with --purge-state.
  --remove-xurl-config Remove ~/.xurl.
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
    --keep-mcp-config)
      REMOVE_MCP_CONFIG=0
      shift
      ;;
    --remove-xurl-app)
      REMOVE_XURL_APP=1
      shift
      ;;
    --keep-xurl-app)
      REMOVE_XURL_APP=0
      shift
      ;;
    --uninstall-xurl)
      UNINSTALL_XURL=1
      shift
      ;;
    --keep-xurl)
      UNINSTALL_XURL=0
      shift
      ;;
    --remove-xurl-config)
      REMOVE_XURL_CONFIG=1
      shift
      ;;
    --keep-xurl-config)
      REMOVE_XURL_CONFIG=0
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

  if truthy "$PURGE_STATE"; then
    if [ "$DRY_RUN" = "1" ]; then
      info "Would permanently remove $target"
      info "Would permanently remove $skills_dir/.backups/twitter-mcp*"
    else
      rm -rf "$target"
      if [ -d "$skills_dir/.backups" ]; then
        find "$skills_dir/.backups" -mindepth 1 -maxdepth 1 -name 'twitter-mcp*' -exec rm -rf {} +
      fi
      info "Removed $target"
      info "Removed matching twitter-mcp backups from $skills_dir/.backups"
    fi
    return 0
  fi

  if [ ! -e "$target" ] && [ ! -L "$target" ]; then
    info "twitter-mcp is not installed at $target"
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

remove_xurl_app() {
  if ! truthy "$REMOVE_XURL_APP"; then
    return 0
  fi
  if [ "$DRY_RUN" = "1" ]; then
    info "Would run: xurl auth apps remove $APP_NAME"
    return 0
  fi
  if ! command -v xurl >/dev/null 2>&1; then
    info "xurl not found; skipped xurl app '$APP_NAME' removal."
    return 0
  fi
  if xurl auth apps list 2>/dev/null | sed -n 's/^▸ \([^ ]*\).*/\1/p' | grep -Fx "$APP_NAME" >/dev/null 2>&1; then
    xurl auth apps remove "$APP_NAME"
    info "Removed xurl app '$APP_NAME' and its tokens."
  else
    info "xurl app '$APP_NAME' was not registered."
  fi
}

remove_xurl_config() {
  remove_config="$REMOVE_XURL_CONFIG"
  if [ "$remove_config" = "auto" ]; then
    if truthy "$PURGE_STATE"; then
      remove_config=1
    else
      remove_config=0
    fi
  fi
  if ! truthy "$remove_config"; then
    return 0
  fi
  config_dir="$HOME/.xurl"
  if [ "$DRY_RUN" = "1" ]; then
    info "Would permanently remove $config_dir"
    return 0
  fi
  rm -rf "$config_dir"
  info "Removed $config_dir"
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

remove_xurl_app
remove_xurl_config
remove_xurl
