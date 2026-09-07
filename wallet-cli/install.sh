#!/bin/sh
set -eu

SKILL_NAME="wallet-cli"
CLI_PACKAGE="@tron-walletcli/wallet-cli"
CLI_VERSION="4.13.0"

TAG="${WALLET_CLI_SKILL_TAG:-main}"
REPO="${WALLET_CLI_SKILL_REPO:-https://github.com/BofAI/skills.git}"
CLIENT="${WALLET_CLI_SKILL_CLIENT:-auto}"
SKILLS_DIR_OVERRIDE="${WALLET_CLI_SKILLS_DIR:-}"
SKIP_CLI_INSTALL="${WALLET_CLI_SKIP_CLI_INSTALL:-0}"
ASSUME_YES="${WALLET_CLI_INSTALL_YES:-1}"
DRY_RUN=0
WORKDIR=""
SOURCE_DIR=""
CLI_ACTION="skip"
CURRENT_CLI_VERSION=""

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

require_posix_tools() {
  missing=""
  for tool in mktemp mkdir cp mv rm date dirname; do
    if ! command_exists "$tool"; then
      missing="${missing}${missing:+, }${tool}"
    fi
  done
  if [ "$CLIENT" = "auto" ]; then
    for tool in env grep; do
      if ! command_exists "$tool"; then
        missing="${missing}${missing:+, }${tool}"
      fi
    done
  fi
  [ -z "$missing" ] || fail "Required POSIX tools are missing from PATH: ${missing}. On Windows, use the standard 'npx skills add' installation or run this script from Git Bash/WSL with a complete POSIX PATH."
}

truthy() {
  case "${1:-}" in
    1|true|yes) return 0 ;;
    *) return 1 ;;
  esac
}

usage() {
  cat <<EOF
Usage: install.sh [--client auto|codex|claude|all] [--skills-dir <dir>] [--tag <ref>] [--yes|--ask] [--skill-only] [--dry-run]

Install the ${SKILL_NAME} Skill and ${CLI_PACKAGE}@${CLI_VERSION}. Installation
is non-interactive by default; use --ask to require one confirmation for the
complete plan, or --skill-only to leave global npm packages unchanged.

Options:
  --client            Target client. Default: auto.
  --skills-dir        Override the target Skills directory.
  --tag               Git branch or tag to install. Default: ${TAG}.
  --yes               Install without prompting. This is the default.
  --ask               Show the complete plan and ask once before installation.
  --skill-only        Install only the Skill; do not install or change the npm CLI.
  --skip-cli-install  Alias for --skill-only.
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
    --tag)
      [ "$#" -ge 2 ] || fail "--tag requires a value"
      TAG="$2"
      shift 2
      ;;
    --tag=*)
      TAG="${1#--tag=}"
      shift
      ;;
    --yes)
      ASSUME_YES=1
      shift
      ;;
    --ask)
      ASSUME_YES=0
      shift
      ;;
    --skill-only|--skip-cli-install)
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
if [ "$DRY_RUN" != "1" ]; then
  require_posix_tools
fi

check_node_and_npm() {
  command_exists node || fail "Node.js 20+ is required to install ${CLI_PACKAGE}."
  node_major="$(node -e 'process.stdout.write(String(process.versions.node.split(".")[0]))' 2>/dev/null || printf '0')"
  [ "$node_major" -ge 20 ] 2>/dev/null || fail "Node.js 20+ is required; detected $(node --version 2>/dev/null || printf 'unknown')."
  command_exists npm || fail "npm is required to install ${CLI_PACKAGE}."
}

installed_cli_version() {
  if ! command_exists wallet-cli || ! command_exists npm || ! command_exists node; then
    return 1
  fi
  npm list --global --depth=0 --json "$CLI_PACKAGE" 2>/dev/null |
    node -e '
      let input = "";
      process.stdin.setEncoding("utf8");
      process.stdin.on("data", chunk => input += chunk);
      process.stdin.on("end", () => {
        const data = JSON.parse(input);
        const version = data.dependencies?.[process.argv[1]]?.version;
        if (!version) process.exit(1);
        process.stdout.write(version);
      });
    ' "$CLI_PACKAGE" 2>/dev/null
}

prepare_cli_install() {
  if truthy "$SKIP_CLI_INSTALL"; then
    CLI_ACTION="skip"
    return
  fi

  CURRENT_CLI_VERSION="$(installed_cli_version || true)"
  if [ "$CURRENT_CLI_VERSION" = "$CLI_VERSION" ]; then
    CLI_ACTION="keep"
    return
  fi

  CLI_ACTION="install"
  if [ "$DRY_RUN" != "1" ]; then
    check_node_and_npm
  fi
}

show_plan() {
  printf '\nInstallation plan:\n'
  printf '  Skill source: %s @ %s\n' "$REPO" "$TAG"
  if [ -n "$SKILLS_DIR_OVERRIDE" ]; then
    printf '  Skill target: %s/%s\n' "$SKILLS_DIR_OVERRIDE" "$SKILL_NAME"
  elif [ "$targets" = "all" ]; then
    printf '  Skill targets: %s/%s and %s/%s\n' \
      "$(default_skills_dir codex)" "$SKILL_NAME" \
      "$(default_skills_dir claude)" "$SKILL_NAME"
  else
    printf '  Skill target: %s/%s\n' "$(default_skills_dir "$targets")" "$SKILL_NAME"
  fi

  case "$CLI_ACTION" in
    skip)
      printf '  npm CLI: unchanged (--skill-only)\n'
      ;;
    keep)
      printf '  npm CLI: %s@%s already installed\n' "$CLI_PACKAGE" "$CLI_VERSION"
      ;;
    install)
      if [ -n "$CURRENT_CLI_VERSION" ]; then
        printf '  npm CLI: replace wallet-cli %s with %s@%s globally\n' \
          "$CURRENT_CLI_VERSION" "$CLI_PACKAGE" "$CLI_VERSION"
      else
        printf '  npm CLI: install %s@%s globally\n' "$CLI_PACKAGE" "$CLI_VERSION"
      fi
      ;;
  esac

  if truthy "$ASSUME_YES"; then
    printf '  Confirmation: skipped (--yes is the default)\n'
  else
    printf '  Confirmation: required (--ask)\n'
  fi
}

confirm_plan() {
  if truthy "$ASSUME_YES"; then
    return
  fi

  if ! { exec 3<>/dev/tty; } 2>/dev/null; then
    fail "--ask requires an interactive terminal; rerun with --yes or --dry-run."
  fi

  printf '\nProceed with this installation? [y/N] ' >&3
  answer=""
  IFS= read -r answer <&3 || fail "Unable to read confirmation from the terminal."
  exec 3>&-
  case "$answer" in
    y|Y|yes|YES|Yes) ;;
    *) fail "Installation canceled." ;;
  esac
}

install_cli() {
  case "$CLI_ACTION" in
    skip)
      info "Left global npm packages unchanged."
      return
      ;;
    keep)
      info "${CLI_PACKAGE}@${CLI_VERSION} is already available."
      return
      ;;
  esac

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

if [ "$DRY_RUN" = "1" ]; then
  SOURCE_DIR="<temporary-clone>/${SKILL_NAME}"
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

prepare_cli_install
show_plan

if [ "$DRY_RUN" = "1" ]; then
  printf '\nDry run complete; no Skill files or npm packages were changed.\n'
  exit 0
fi

confirm_plan
install_cli

if [ -n "$SKILLS_DIR_OVERRIDE" ]; then
  install_skill "$SKILLS_DIR_OVERRIDE"
elif [ "$targets" = "all" ]; then
  install_skill "$(default_skills_dir codex)"
  install_skill "$(default_skills_dir claude)"
else
  install_skill "$(default_skills_dir "$targets")"
fi

printf '\n%s installed.\n' "$SKILL_NAME"
if [ "$CLI_ACTION" = "skip" ]; then
  printf 'The npm CLI was left unchanged; install %s@%s before using the Skill.\n' \
    "$CLI_PACKAGE" "$CLI_VERSION"
else
  printf 'Verified CLI: wallet-cli %s\n' "$(installed_cli_version)"
fi
