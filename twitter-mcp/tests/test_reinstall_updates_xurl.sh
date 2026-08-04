#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/twitter-mcp-test.XXXXXX")"
MOCK_BIN="$TEST_ROOT/bin"
LOG="$TEST_ROOT/commands.log"
mkdir -p "$MOCK_BIN" "$TEST_ROOT/home"

cat >"$MOCK_BIN/xurl" <<'EOF'
#!/bin/bash
set -eu
printf 'xurl %s\n' "$*" >>"$TEST_COMMAND_LOG"
case "$*" in
  "auth apps list") printf '▸ xmcp  [client_id: test]\n' ;;
  "token --app xmcp") exit 0 ;;
  "--version") printf 'xurl version 1.2.2\n' ;;
  "auth default xmcp") exit 0 ;;
  *"auth apps add"*|*"auth oauth2"*) exit 91 ;;
esac
EOF

cat >"$MOCK_BIN/npm" <<'EOF'
#!/bin/bash
set -eu
printf 'npm %s\n' "$*" >>"$TEST_COMMAND_LOG"
EOF

cat >"$MOCK_BIN/node" <<'EOF'
#!/bin/bash
printf 'v20.0.0\n'
EOF

chmod 700 "$MOCK_BIN/xurl" "$MOCK_BIN/npm" "$MOCK_BIN/node"

PATH="$MOCK_BIN:/usr/bin:/bin" \
HOME="$TEST_ROOT/home" \
TEST_COMMAND_LOG="$LOG" \
X_MCP_APP_NAME=xmcp \
X_MCP_REGISTER_CODEX=0 \
X_MCP_REGISTER_CLAUDE=0 \
XMCP_VERSION=latest \
/bin/bash "$ROOT/twitter-mcp/scripts/install_xmcp.sh" >/dev/null

grep -Fx 'npm install -g @xdevplatform/xurl@latest' "$LOG" >/dev/null
grep -Fx 'xurl token --app xmcp' "$LOG" >/dev/null
grep -Fx 'xurl auth default xmcp' "$LOG" >/dev/null
if grep -E 'auth apps add|auth oauth2' "$LOG" >/dev/null; then
  printf 'OAuth configuration unexpectedly ran during reinstall.\n' >&2
  exit 1
fi

printf 'twitter-mcp reinstall update test passed.\n'
