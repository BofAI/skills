#!/bin/sh
set -eu

SKILL_NAME="wallet-cli"
CLI_PACKAGE="@tron-walletcli/wallet-cli"
CLI_VERSION="4.12.0"

TAG="${WALLET_CLI_SKILL_TAG:-main}"
REPO="${WALLET_CLI_SKILL_REPO:-https://github.com/BofAI/skills.git}"
CLIENT="${WALLET_CLI_SKILL_CLIENT:-auto}"
SKILLS_DIR_OVERRIDE="${WALLET_CLI_SKILLS_DIR:-}"
SKIP_CLI_INSTALL="${WALLET_CLI_SKIP_CLI_INSTALL:-0}"
DRY_RUN=0
WORKDIR=""

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

truthy() {
  case "${1:-}" in
    1|true|yes) return 0 ;;
    *) return 1 ;;
  esac
}

usage() {
  cat <<EOF
Usage: install.sh [--client auto|codex|claude|all] [--skills-dir <dir>] [--skip-cli-install] [--dry-run]

Install the ${SKILL_NAME} Skill. Unless --skip-cli-install is used, the script
asks for confirmation before installing ${CLI_PACKAGE}@${CLI_VERSION} globally.

Options:
  --client            Target client. Default: auto.
  --skills-dir        Override the target Skills directory.
  --skip-cli-install  Install the Skill without offering to install the npm CLI.
  --dry-run           Preview actions without changing files or packages.
  -h, --help          Show this help.
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
    --skills-dir)
      [ "$#" -ge 2 ] || fail "--skills-dir requires a value"
      SKILLS_DIR_OVERRIDE="$2"
      shift 2
      ;;
    --skills-dir=*)
      SKILLS_DIR_OVERRIDE="${1#--skills-dir=}"
      shift
      ;;
    --skip-cli-install)
      SKIP_CLI_INSTALL=1
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

command_exists git || fail "git is required to install ${SKILL_NAME}."

check_node_and_npm() {
  command_exists node || fail "Node.js 20+ is required to install ${CLI_PACKAGE}."
  node_major="$(node -e 'process.stdout.write(String(process.versions.node.split(".")[0]))' 2>/dev/null || printf '0')"
  [ "$node_major" -ge 20 ] 2>/dev/null || fail "Node.js 20+ is required; detected $(node --version 2>/dev/null || printf 'unknown')."
  command_exists npm || fail "npm is required to install ${CLI_PACKAGE}."
}

installed_cli_version() {
  if ! command_exists wallet-cli; then
    return 1
  fi
  wallet-cli --version 2>/dev/null
}

confirm_cli_install() {
  if [ ! -r /dev/tty ]; then
    info "No interactive terminal is available; skipping global npm installation."
    return 1
  fi

  printf '\nInstall %s@%s globally with npm? [y/N] ' "$CLI_PACKAGE" "$CLI_VERSION" >/dev/tty
  answer=""
  IFS= read -r answer </dev/tty || return 1
  case "$answer" in
    y|Y|yes|YES|Yes) return 0 ;;
    *) return 1 ;;
  esac
}

install_cli_if_approved() {
  if truthy "$SKIP_CLI_INSTALL"; then
    info "Skipped npm CLI installation by request."
    return
  fi

  current_version="$(installed_cli_version || true)"
  if [ "$current_version" = "$CLI_VERSION" ]; then
    info "${CLI_PACKAGE}@${CLI_VERSION} is already available."
    return
  fi

  if [ -n "$current_version" ]; then
    info "Detected wallet-cli ${current_version}; this Skill requires ${CLI_VERSION}."
  else
    info "wallet-cli is not currently available on PATH."
  fi

  if [ "$DRY_RUN" = "1" ]; then
    info "Would ask before running: npm install --global --no-fund --no-audit ${CLI_PACKAGE}@${CLI_VERSION}"
    return
  fi

  if ! confirm_cli_install; then
    info "Global npm installation was not approved; continuing with Skill-only installation."
    return
  fi

  check_node_and_npm
  npm install --global --no-fund --no-audit "${CLI_PACKAGE}@${CLI_VERSION}"
  installed_version="$(installed_cli_version || true)"
  [ "$installed_version" = "$CLI_VERSION" ] || fail "Expected wallet-cli ${CLI_VERSION}, found ${installed_version:-unknown}."
  info "Installed ${CLI_PACKAGE}@${installed_version}."
}

cleanup() {
  if [ -n "$WORKDIR" ] && [ -d "$WORKDIR" ]; then
    rm -rf "$WORKDIR"
  fi
}

interrupted() {
  trap - 0 HUP INT TERM
  cleanup
  exit 1
}

trap cleanup 0
trap interrupted HUP INT TERM

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
  case "$1" in
    codex) printf '%s/.codex/skills' "$HOME" ;;
    claude) printf '%s/.claude/skills' "$HOME" ;;
    *) fail "Unknown client: $1" ;;
  esac
}

next_backup_path() {
  skills_dir="$1"
  stamp="$(date +%Y%m%d-%H%M%S)"
  backup="$skills_dir/.backups/${SKILL_NAME}-$stamp"
  suffix=1
  while [ -e "$backup" ] || [ -L "$backup" ]; do
    suffix=$((suffix + 1))
    backup="$skills_dir/.backups/${SKILL_NAME}-$stamp-$suffix"
  done
  printf '%s' "$backup"
}

install_skill() {
  skills_dir="$1"
  target="$skills_dir/${SKILL_NAME}"

  if [ "$DRY_RUN" = "1" ]; then
    info "Would install ${SKILL_NAME} to $target"
    if [ -e "$target" ] || [ -L "$target" ]; then
      info "Would preserve the existing install under $skills_dir/.backups/"
    fi
    return
  fi

  mkdir -p "$skills_dir"
  if [ -e "$target" ] || [ -L "$target" ]; then
    backup="$(next_backup_path "$skills_dir")"
    mkdir -p "$(dirname "$backup")"
    mv "$target" "$backup"
    info "Moved the existing Skill to $backup"
  fi

  cp -R "$SOURCE_DIR" "$target"
  info "Installed Skill at $target"
}

install_cli_if_approved

if [ "$DRY_RUN" = "1" ]; then
  SOURCE_DIR="<temporary-clone>/${SKILL_NAME}"
  info "Would clone ${REPO} at ${TAG} into a temporary directory"
else
  WORKDIR="$(mktemp -d 2>/dev/null || mktemp -d -t "${SKILL_NAME}-install")"
  clone_dir="$WORKDIR/skills"
  info "Cloning ${REPO} at ${TAG}"
  git clone --depth 1 --branch "$TAG" "$REPO" "$clone_dir"
  SOURCE_DIR="$clone_dir/${SKILL_NAME}"
  [ -f "$SOURCE_DIR/SKILL.md" ] || fail "${SKILL_NAME}/SKILL.md was not found in the cloned repository."
fi

targets="$CLIENT"
if [ "$CLIENT" = "auto" ]; then
  targets="$(detect_client)"
fi

if [ -n "$SKILLS_DIR_OVERRIDE" ]; then
  install_skill "$SKILLS_DIR_OVERRIDE"
elif [ "$targets" = "all" ]; then
  install_skill "$(default_skills_dir codex)"
  install_skill "$(default_skills_dir claude)"
else
  install_skill "$(default_skills_dir "$targets")"
fi

if [ "$DRY_RUN" = "1" ]; then
  printf '\nDry run complete; no Skill files or npm packages were changed.\n'
else
  printf '\n%s installed.\n' "$SKILL_NAME"
  printf 'Verify the CLI with: wallet-cli --version\n'
  if [ "$(installed_cli_version || true)" != "$CLI_VERSION" ]; then
    printf 'The npm CLI is not pinned to %s; install it explicitly before using the Skill.\n' "$CLI_VERSION"
  fi
fi
