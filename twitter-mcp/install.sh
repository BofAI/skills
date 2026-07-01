#!/bin/sh
set -eu

TAG="${X_MCP_INSTALL_TAG:-v1.5.11-beta.16}"
BASE_URL="${X_MCP_INSTALL_BASE_URL:-https://raw.githubusercontent.com/BofAI/skills/${TAG}/twitter-mcp}"
REGISTER_CODEX="${X_MCP_REGISTER_CODEX:-1}"
REGISTER_CLAUDE="${X_MCP_REGISTER_CLAUDE:-auto}"
REGISTER_CODEX_MCP="${X_MCP_REGISTER_CODEX_MCP:-0}"
REGISTER_CLAUDE_MCP="${X_MCP_REGISTER_CLAUDE_MCP:-0}"

info() {
  printf '==> %s\n' "$1"
}

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

truthy() {
  case "${1:-}" in
    1|true|yes) return 0 ;;
    *) return 1 ;;
  esac
}

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
  info "Existing twitter-mcp skill moved to $backup"
}

install_skill_copy() {
  skills_dir="$1"
  target="$skills_dir/twitter-mcp"
  staging="$WORKDIR/twitter-mcp-skill"
  rm -rf "$staging"
  mkdir -p "$staging/scripts" "$staging/agents"
  download_file "${BASE_URL%/}/SKILL.md" "$staging/SKILL.md"
  download_file "${BASE_URL%/}/install.sh" "$staging/install.sh"
  download_file "${BASE_URL%/}/agents/openai.yaml" "$staging/agents/openai.yaml"
  download_file "${BASE_URL%/}/scripts/install_xmcp.sh" "$staging/scripts/install_xmcp.sh"
  chmod 700 "$staging/install.sh" "$staging/scripts/install_xmcp.sh"
  mkdir -p "$skills_dir"
  backup_existing_skill "$target" "$skills_dir"
  mv "$staging" "$target"
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
X_MCP_REGISTER_CODEX="$REGISTER_CODEX_MCP" X_MCP_REGISTER_CLAUDE="$REGISTER_CLAUDE_MCP" exec /bin/bash "$INSTALLER" "$@"
