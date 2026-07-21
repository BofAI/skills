#!/bin/sh
set -eu

CLIENT="${X402_UNINSTALL_CLIENT:-auto}"
PURGE_STATE="${X402_PURGE_STATE:-0}"
REMOVE_DEV_SRC="${X402_REMOVE_DEV_SRC:-auto}"
DRY_RUN=0
SKILLS_DIR_OVERRIDE="${X402_SKILLS_DIR:-}"

SKILL_NAME="x402-payment"

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
  cat <<EOF
Usage: uninstall.sh [--client auto|codex|claude|all] [--skills-dir <dir>] [--purge-state] [--remove-dev-src] [--keep-dev-src] [--dry-run]

Default uninstall moves installed ${SKILL_NAME} skill directories to .backups/
and disables SKILL.md, preserving configuration in the backup. With --purge-state,
the active install and existing ${SKILL_NAME} backups are permanently removed.

Options:
  --client          Target client. Default: auto.
  --skills-dir      Override the target skills directory.
  --purge-state     Permanently remove the installed skill directory, config, and matching backups.
  --remove-dev-src   Remove the persistent dev source directory (\$HOME/.local/share/${SKILL_NAME}-src).
  --keep-dev-src     Keep the persistent dev source directory (default unless --symlink was used).
  --dry-run          Print actions without changing files.
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
    --skills-dir)
      [ "$#" -ge 2 ] || fail "--skills-dir requires a value"
      SKILLS_DIR_OVERRIDE="$2"
      shift 2
      ;;
    --skills-dir=*)
      SKILLS_DIR_OVERRIDE="${1#--skills-dir=}"
      shift
      ;;
    --remove-dev-src)
      REMOVE_DEV_SRC=1
      shift
      ;;
    --keep-dev-src)
      REMOVE_DEV_SRC=0
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

backup_target() {
  skills_dir="$1"
  target="$skills_dir/${SKILL_NAME}"

  if truthy "$PURGE_STATE"; then
    if [ "$DRY_RUN" = "1" ]; then
      info "Would permanently remove $target"
      info "Would permanently remove $skills_dir/.backups/${SKILL_NAME}*"
    else
      rm -rf "$target"
      if [ -d "$skills_dir/.backups" ]; then
        find "$skills_dir/.backups" -mindepth 1 -maxdepth 1 -name "${SKILL_NAME}*" -exec rm -rf {} +
      fi
      info "Removed $target"
      info "Removed matching ${SKILL_NAME} backups from $skills_dir/.backups"
    fi
    return 0
  fi

  if [ ! -e "$target" ] && [ ! -L "$target" ]; then
    info "${SKILL_NAME} is not installed at $target"
    return 0
  fi

  backup_dir="$skills_dir/.backups"
  stamp="$(date +%Y%m%d-%H%M%S)"
  backup="$backup_dir/${SKILL_NAME}-uninstalled-$stamp"
  suffix=1
  while [ -e "$backup" ] || [ -L "$backup" ]; do
    suffix=$((suffix + 1))
    backup="$backup_dir/${SKILL_NAME}-uninstalled-$stamp-$suffix"
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
  info "Uninstalled ${SKILL_NAME} from $target"
  info "Preserved previous install and config at $backup"
}

remove_dev_src() {
  remove="$REMOVE_DEV_SRC"
  if [ "$remove" = "auto" ]; then
    if truthy "$PURGE_STATE"; then
      remove=1
    else
      remove=0
    fi
  fi
  if ! truthy "$remove"; then
    return 0
  fi
  dev_src="$HOME/.local/share/${SKILL_NAME}-src"
  if [ "$DRY_RUN" = "1" ]; then
    info "Would remove $dev_src"
    return 0
  fi
  if [ -d "$dev_src" ] || [ -L "$dev_src" ]; then
    rm -rf "$dev_src"
    info "Removed dev source directory $dev_src"
  else
    info "Dev source directory $dev_src not found"
  fi
}

targets="$CLIENT"
if [ "$CLIENT" = "auto" ]; then
  targets="$(detect_client)"
fi

if [ -n "$SKILLS_DIR_OVERRIDE" ]; then
  backup_target "$SKILLS_DIR_OVERRIDE"
else
  case "$targets" in
    codex)
      backup_target "$HOME/.codex/skills"
      ;;
    claude)
      backup_target "$HOME/.claude/skills"
      ;;
    all)
      backup_target "$HOME/.codex/skills"
      backup_target "$HOME/.claude/skills"
      ;;
  esac
fi

remove_dev_src

cat <<EOF

${SKILL_NAME} uninstalled.

Reinstall at any time with:
  curl -fsSL https://raw.githubusercontent.com/BofAI/skills/main/${SKILL_NAME}/install.sh | sh

Backups (if any) are preserved under <skills-dir>/.backups/${SKILL_NAME}-*.
EOF
