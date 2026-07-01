#!/bin/sh
set -eu

TAG="${X_MCP_INSTALL_TAG:-v1.5.11-beta.3}"
BASE_URL="${X_MCP_INSTALL_BASE_URL:-https://raw.githubusercontent.com/BofAI/skills/${TAG}/twitter-mcp}"

if command -v mktemp >/dev/null 2>&1; then
  WORKDIR="$(mktemp -d 2>/dev/null || mktemp -d -t twitter-mcp)"
else
  WORKDIR="${TMPDIR:-/tmp}/twitter-mcp-install.$$"
  mkdir -p "$WORKDIR"
fi

INSTALLER="$WORKDIR/install_xmcp.sh"
INSTALLER_URL="${BASE_URL%/}/scripts/install_xmcp.sh"

if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$INSTALLER_URL" -o "$INSTALLER"
elif command -v wget >/dev/null 2>&1; then
  wget -qO "$INSTALLER" "$INSTALLER_URL"
else
  printf 'Error: curl or wget is required to download %s\n' "$INSTALLER_URL" >&2
  exit 1
fi

chmod 700 "$INSTALLER"
exec /bin/bash "$INSTALLER" "$@"
