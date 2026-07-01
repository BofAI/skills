#!/bin/sh
set -eu

TAG="${TWITTER_DIGEST_INSTALL_TAG:-v1.5.11-beta.16}"
REPO="${TWITTER_DIGEST_INSTALL_REPO:-https://github.com/BofAI/skills.git}"
CLIENT="${TWITTER_DIGEST_INSTALL_CLIENT:-auto}"
ALLOW_CLAUDE_COMMANDS="${TWITTER_DIGEST_ALLOW_CLAUDE_COMMANDS:-0}"
ALLOW_CLAUDE_STATE_READ="${TWITTER_DIGEST_ALLOW_CLAUDE_STATE_READ:-0}"
SKIP_BROWSER_CHECK="${TWITTER_DIGEST_SKIP_BROWSER_CHECK:-0}"

info() {
  printf '==> %s\n' "$1"
}

truthy() {
  case "${1:-}" in
    1|true|yes) return 0 ;;
    *) return 1 ;;
  esac
}

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
