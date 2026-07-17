#!/bin/sh
set -eu

TAG="${X402_INSTALL_TAG:-main}"
REPO="${X402_INSTALL_REPO:-https://github.com/BofAI/skills.git}"
CLIENT="${X402_INSTALL_CLIENT:-auto}"
SYMLINK="${X402_SYMLINK:-0}"
SKIP_CLI_INSTALL="${X402_SKIP_CLI_INSTALL:-0}"
SKIP_NODE_CHECK="${X402_SKIP_NODE_CHECK:-0}"
OPEN_TERMINAL="${X402_OPEN_TERMINAL:-auto}"

SKILL_NAME="x402-payment"
CLI_PACKAGE="@bankofai/x402-cli"
CLI_VERSION="${X402_CLI_VERSION:-1.0.1-beta.6}"

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

usage() {
  cat <<EOF
Usage: install.sh [--client auto|codex|claude|all] [--symlink] [--skip-cli-install] [--skip-node-check] [--skills-dir <dir>] [--dry-run] [-h]

Install the ${SKILL_NAME} skill into the target agent client's local skills directory.

Options:
  --client          Target client. Default: auto (detected from environment).
  --symlink         Install as a symlink to a persistent dev source directory instead of copying.
  --skip-cli-install   Skip installing ${CLI_PACKAGE}@${CLI_VERSION} globally.
  --skip-node-check    Skip the Node.js 20+ and npm availability check.
  --skills-dir      Override the target skills directory.
  --dry-run         Print actions without changing files.
EOF
}

DRY_RUN=0
SKILLS_DIR_OVERRIDE="${X402_SKILLS_DIR:-}"

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
    --symlink)
      SYMLINK=1
      shift
      ;;
    --skip-cli-install|--skip-npm-install)
      SKIP_CLI_INSTALL=1
      shift
      ;;
    --skip-node-check)
      SKIP_NODE_CHECK=1
      shift
      ;;
    --skills-dir)
      [ "$#" -ge 2 ] || fail "--skills-dir requires a value"
      SKILLS_DIR_OVERRIDE="$2"
      shift 2
      ;;
    --skills-dir=*)
      SKILLS_DIR_OVERRIDE="${1#--skills-dir=}"
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
  if [ "${X402_TERMINAL_CHILD:-}" = "1" ]; then
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

  installer_url="https://raw.githubusercontent.com/BofAI/skills/${TAG}/${SKILL_NAME}/install.sh"
  command_text="cd ~ && TMPDIR=\"\$(mktemp -d)\" && INSTALL_SH=\"\$TMPDIR/${SKILL_NAME}-install.sh\" && curl -fsSL $(shell_quote "$installer_url") -o \"\$INSTALL_SH\" && chmod 700 \"\$INSTALL_SH\" && env X402_TERMINAL_CHILD=1 X402_OPEN_TERMINAL=0 X402_INSTALL_TAG=$(shell_quote "$TAG") X402_INSTALL_REPO=$(shell_quote "$REPO") X402_INSTALL_CLIENT=$(shell_quote "$CLIENT") X402_SYMLINK=$(shell_quote "$SYMLINK") X402_SKIP_CLI_INSTALL=$(shell_quote "$SKIP_CLI_INSTALL") X402_SKIP_NODE_CHECK=$(shell_quote "$SKIP_NODE_CHECK") X402_CLI_VERSION=$(shell_quote "$CLI_VERSION") X402_SKILLS_DIR=$(shell_quote "$SKILLS_DIR_OVERRIDE") /bin/sh \"\$INSTALL_SH\"; STATUS=\$?; rm -rf \"\$TMPDIR\"; printf '\\nPress Enter to close this window...'; IFS= read -r _; exit \"\$STATUS\""
  osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$(applescript_quote "$command_text")"
end tell
OSA
  info "Opened Terminal for ${SKILL_NAME} installation. Continue there."
  exit 0
}

if [ "$DRY_RUN" != "1" ] && should_open_terminal; then
  open_self_in_terminal_and_exit "$@"
fi

# ---------------------------------------------------------------------------
# Runtime checks
# ---------------------------------------------------------------------------

if ! command_exists git; then
  fail "git is required to install ${SKILL_NAME}."
fi

if ! truthy "$SKIP_NODE_CHECK"; then
  if ! command_exists node; then
    fail "Node.js 20+ is required to install ${SKILL_NAME}. Install it from https://nodejs.org/ and rerun."
  fi
  node_major="$(node -e 'process.stdout.write(String(process.versions.node.split(".")[0]))' 2>/dev/null || echo 0)"
  if [ "$node_major" -lt 20 ] 2>/dev/null; then
    fail "Node.js 20+ is required (detected v${node_major}). Upgrade from https://nodejs.org/ and rerun."
  fi
  info "Node.js v$(node -v | sed 's/^v//') detected."
  if ! command_exists npm; then
    fail "npm is required to install ${SKILL_NAME} dependencies. It ships with Node.js 20+."
  fi
fi

if truthy "$SKIP_CLI_INSTALL"; then
  info "Skipped ${CLI_PACKAGE} installation."
elif [ "$DRY_RUN" = "1" ]; then
  info "Would install ${CLI_PACKAGE}@${CLI_VERSION} globally"
else
  info "Installing ${CLI_PACKAGE}@${CLI_VERSION}"
  npm install --global --no-fund --no-audit "${CLI_PACKAGE}@${CLI_VERSION}"
  command_exists x402-cli || fail "x402-cli was installed but is not available on PATH."
  installed_version="$(x402-cli --version 2>/dev/null || true)"
  [ "$installed_version" = "$CLI_VERSION" ] || fail "Expected x402-cli ${CLI_VERSION}, found ${installed_version:-unknown}."
  info "Installed ${installed_version}"
fi

# ---------------------------------------------------------------------------
# Clone the repository
# ---------------------------------------------------------------------------

if command_exists mktemp; then
  WORKDIR="$(mktemp -d 2>/dev/null || mktemp -d -t "${SKILL_NAME}")"
else
  WORKDIR="${TMPDIR:-/tmp}/${SKILL_NAME}-install.$$"
  mkdir -p "$WORKDIR"
fi

cleanup() {
  rm -rf "$WORKDIR"
}
interrupted() {
  trap - 0 HUP INT TERM
  cleanup
  exit 1
}
trap cleanup 0
trap interrupted HUP INT TERM

CLONE_DIR="$WORKDIR/skills"
if [ "$DRY_RUN" = "1" ]; then
  info "Would clone ${REPO} (tag ${TAG}) to ${CLONE_DIR}"
else
  info "Cloning ${REPO} at ${TAG}"
  git clone --depth 1 --branch "$TAG" "$REPO" "$CLONE_DIR"
fi

SRC_DIR="$CLONE_DIR/${SKILL_NAME}"
if [ "$DRY_RUN" = "0" ] && [ ! -d "$SRC_DIR" ]; then
  fail "${SKILL_NAME} directory not found in the cloned repository at ${SRC_DIR}."
fi

# ---------------------------------------------------------------------------
# Client detection
# ---------------------------------------------------------------------------

detect_client() {
  if env | grep -q '^CODEX_'; then
    printf 'codex'
    return
  fi
  if env | grep -q '^CLAUDE'; then
    printf 'claude'
    return
  fi
  if [ -d "$HOME/.codex/skills/${SKILL_NAME}" ] && [ ! -d "$HOME/.claude/skills/${SKILL_NAME}" ]; then
    printf 'codex'
    return
  fi
  if [ -d "$HOME/.claude/skills/${SKILL_NAME}" ] && [ ! -d "$HOME/.codex/skills/${SKILL_NAME}" ]; then
    printf 'claude'
    return
  fi
  printf 'all'
}

default_skills_dir() {
  client="$1"
  if [ "$client" = "codex" ]; then
    printf '%s/.codex/skills' "$HOME"
  else
    printf '%s/.claude/skills' "$HOME"
  fi
}

# ---------------------------------------------------------------------------
# Backup / install helpers
# ---------------------------------------------------------------------------

backup_path() {
  skills_dir="$1"
  stamp="$(date +%Y%m%d-%H%M%S)"
  backup_dir="$skills_dir/.backups"
  candidate="$backup_dir/${SKILL_NAME}-uninstalled-$stamp"
  suffix=1
  while [ -e "$candidate" ] || [ -L "$candidate" ]; do
    suffix=$((suffix + 1))
    candidate="$backup_dir/${SKILL_NAME}-uninstalled-$stamp-$suffix"
  done
  printf '%s' "$candidate"
}

backup_existing_skill() {
  target="$1"
  skills_dir="$2"
  BACKUP_CREATED=""
  if [ ! -e "$target" ] && [ ! -L "$target" ]; then
    return 0
  fi
  backup="$(backup_path "$skills_dir")"
  if [ "$DRY_RUN" = "1" ]; then
    info "Would move existing install to backup: $backup"
    return 0
  fi
  mkdir -p "$(dirname "$backup")"
  mv "$target" "$backup"
  if [ -f "$backup/SKILL.md" ]; then
    mv "$backup/SKILL.md" "$backup/SKILL.md.disabled"
  fi
  BACKUP_CREATED="$backup"
  info "Existing ${SKILL_NAME} moved to $backup"
}

restore_config() {
  backup="$1"
  target="$2"
  if [ -z "$backup" ] || [ ! -d "$backup" ]; then
    return 0
  fi
  if [ -f "$backup/x402-config.json" ] && [ ! -e "$target/x402-config.json" ]; then
    cp "$backup/x402-config.json" "$target/x402-config.json"
    info "Preserved x402-config.json from previous install."
  fi
}

install_skill() {
  skills_dir="$1"
  target="$skills_dir/${SKILL_NAME}"

  if [ "$DRY_RUN" = "1" ]; then
    info "Would install ${SKILL_NAME} to $target"
    if truthy "$SYMLINK"; then
      info "Would create symlink to persistent dev source."
    fi
    return 0
  fi

  mkdir -p "$skills_dir"
  BACKUP_CREATED=""
  backup_existing_skill "$target" "$skills_dir"
  RESTORED_BACKUP="$BACKUP_CREATED"

  if truthy "$SYMLINK"; then
    # Persist the clone so the symlink remains valid after this script exits.
    dev_src="$HOME/.local/share/${SKILL_NAME}-src"
    rm -rf "$dev_src"
    mkdir -p "$(dirname "$dev_src")"
    cp -R "$SRC_DIR" "$dev_src"
    rm -rf "$dev_src/node_modules" "$dev_src/.git"
    ln -sfn "$dev_src" "$target"
    info "Linked skill: $target -> $dev_src"
    install_dir="$dev_src"
  else
    rm -rf "$target"
    cp -R "$SRC_DIR" "$target"
    rm -rf "$target/node_modules" "$target/.git" "$target/dist"
    info "Copied skill to $target"
    install_dir="$target"
  fi

  restore_config "$RESTORED_BACKUP" "$install_dir"

  info "Installed skill path: $target"
  info "Verify with: x402-cli --version"
}

# ---------------------------------------------------------------------------
# Resolve targets and install
# ---------------------------------------------------------------------------

targets="$CLIENT"
if [ "$CLIENT" = "auto" ]; then
  targets="$(detect_client)"
fi

if [ -n "$SKILLS_DIR_OVERRIDE" ]; then
  install_skill "$SKILLS_DIR_OVERRIDE"
elif [ "$targets" = "all" ]; then
  for client in codex claude; do
    install_skill "$(default_skills_dir "$client")"
  done
else
  install_skill "$(default_skills_dir "$targets")"
fi

# ---------------------------------------------------------------------------
# Post-install guidance
# ---------------------------------------------------------------------------

cat <<EOF

${SKILL_NAME} installed successfully.

Next steps:
  1. Configure your wallet via agent-wallet (set AGENT_WALLET_PASSWORD or
     AGENT_WALLET_PRIVATE_KEY). Run: agent-wallet list
  2. Optional: set TRON_GRID_API_KEY for TRON mainnet reliability.
  3. Verify the installation with: x402-cli --version

For full usage instructions see SKILL.md in the installed skill directory.
EOF
