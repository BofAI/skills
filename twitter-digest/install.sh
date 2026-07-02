#!/bin/sh
set -eu

TAG="${TWITTER_DIGEST_INSTALL_TAG:-v1.5.12-beta.8}"
REPO="${TWITTER_DIGEST_INSTALL_REPO:-https://github.com/BofAI/skills.git}"
CLIENT="${TWITTER_DIGEST_INSTALL_CLIENT:-auto}"
ALLOW_CLAUDE_COMMANDS="${TWITTER_DIGEST_ALLOW_CLAUDE_COMMANDS:-0}"
ALLOW_CLAUDE_STATE_READ="${TWITTER_DIGEST_ALLOW_CLAUDE_STATE_READ:-0}"
SKIP_BROWSER_CHECK="${TWITTER_DIGEST_SKIP_BROWSER_CHECK:-0}"
OPEN_TERMINAL="${TWITTER_DIGEST_OPEN_TERMINAL:-auto}"

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

should_open_terminal() {
  if [ "${TWITTER_DIGEST_TERMINAL_CHILD:-}" = "1" ]; then
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

  installer_url="https://raw.githubusercontent.com/BofAI/skills/${TAG}/twitter-digest/install.sh"
  args_text=""
  for arg in "$@"; do
    args_text="${args_text} $(shell_quote "$arg")"
  done
  command_text="cd ~ && TMPDIR=\"\$(mktemp -d)\" && INSTALL_SH=\"\$TMPDIR/twitter-digest-install.sh\" && curl -fsSL $(shell_quote "$installer_url") -o \"\$INSTALL_SH\" && chmod 700 \"\$INSTALL_SH\" && env TWITTER_DIGEST_TERMINAL_CHILD=1 TWITTER_DIGEST_OPEN_TERMINAL=0 TWITTER_DIGEST_INSTALL_TAG=$(shell_quote "$TAG") TWITTER_DIGEST_INSTALL_REPO=$(shell_quote "$REPO") TWITTER_DIGEST_INSTALL_CLIENT=$(shell_quote "$CLIENT") TWITTER_DIGEST_ALLOW_CLAUDE_COMMANDS=$(shell_quote "$ALLOW_CLAUDE_COMMANDS") TWITTER_DIGEST_ALLOW_CLAUDE_STATE_READ=$(shell_quote "$ALLOW_CLAUDE_STATE_READ") TWITTER_DIGEST_SKIP_BROWSER_CHECK=$(shell_quote "$SKIP_BROWSER_CHECK") /bin/sh \"\$INSTALL_SH\"${args_text}; printf '\\nPress Enter to close this window...'; IFS= read -r _"
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
  open_self_in_terminal_and_exit "$@"
fi

if ! command -v git >/dev/null 2>&1; then
  printf 'Error: git is required to install twitter-digest.\n' >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  printf 'Error: python3 is required to install twitter-digest.\n' >&2
  exit 1
fi

if command -v mktemp >/dev/null 2>&1; then
  WORKDIR="$(mktemp -d 2>/dev/null || mktemp -d -t twitter-digest)"
else
  WORKDIR="${TMPDIR:-/tmp}/twitter-digest-install.$$"
  mkdir -p "$WORKDIR"
fi

CLONE_DIR="$WORKDIR/skills"
info "Cloning ${REPO} at ${TAG}"
git clone --depth 1 --branch "$TAG" "$REPO" "$CLONE_DIR"

args=""
case "$CLIENT" in
  auto|codex|claude) args="$args --client $CLIENT" ;;
  *) printf 'Error: TWITTER_DIGEST_INSTALL_CLIENT must be auto, codex, or claude.\n' >&2; exit 1 ;;
esac

if truthy "$ALLOW_CLAUDE_COMMANDS"; then
  args="$args --allow-claude-commands"
fi

if truthy "$ALLOW_CLAUDE_STATE_READ"; then
  args="$args --allow-claude-state-read"
fi

if truthy "$SKIP_BROWSER_CHECK"; then
  args="$args --skip-browser-check"
fi

info "Running twitter-digest installer"
# shellcheck disable=SC2086
exec python3 "$CLONE_DIR/twitter-digest/scripts/install.py" $args "$@"
