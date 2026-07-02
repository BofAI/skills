#!/bin/sh
set -eu

CLIENT="${TWITTER_DIGEST_UNINSTALL_CLIENT:-auto}"
PURGE_STATE="${TWITTER_DIGEST_PURGE_STATE:-0}"
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
Usage: uninstall.sh [--client auto|codex|claude|all] [--purge-state] [--dry-run]

Default uninstall moves installed twitter-digest skill directories to .backups/
and disables SKILL.md, preserving .state in the backup.

Options:
  --client        Target client. Default: auto.
  --purge-state   Permanently remove the installed skill directory, including .state.
  --dry-run       Print actions without changing files.
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
  if [ -d "$HOME/.codex/skills/twitter-digest" ] && [ ! -d "$HOME/.claude/skills/twitter-digest" ]; then
    printf 'codex'
    return
  fi
  if [ -d "$HOME/.claude/skills/twitter-digest" ] && [ ! -d "$HOME/.codex/skills/twitter-digest" ]; then
    printf 'claude'
    return
  fi
  printf 'all'
}

backup_target() {
  skills_dir="$1"
  target="$skills_dir/twitter-digest"
  if [ ! -e "$target" ] && [ ! -L "$target" ]; then
    info "twitter-digest is not installed at $target"
    return 0
  fi

  if truthy "$PURGE_STATE"; then
    if [ "$DRY_RUN" = "1" ]; then
      info "Would permanently remove $target"
    else
      rm -rf "$target"
      info "Removed $target"
    fi
    return 0
  fi

  backup_dir="$skills_dir/.backups"
  stamp="$(date +%Y%m%d-%H%M%S)"
  backup="$backup_dir/twitter-digest-uninstalled-$stamp"
  suffix=1
  while [ -e "$backup" ] || [ -L "$backup" ]; do
    suffix=$((suffix + 1))
    backup="$backup_dir/twitter-digest-uninstalled-$stamp-$suffix"
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
  info "Uninstalled twitter-digest from $target"
  info "Preserved previous install and .state at $backup"
}

targets="$CLIENT"
if [ "$CLIENT" = "auto" ]; then
  targets="$(detect_client)"
fi

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
