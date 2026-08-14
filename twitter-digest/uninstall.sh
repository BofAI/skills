#!/bin/sh
set -eu

CLIENT="${TWITTER_DIGEST_UNINSTALL_CLIENT:-auto}"
DRY_RUN=0

info() {
  printf '==> %s\n' "$1"
}

fail() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage: uninstall.sh [--client auto|codex|claude|all] [--dry-run]

Moves the installed twitter-digest skill and its bundled xurl binary into the
client's .backups directory. Existing authorization and Chat keys in ~/.xurl
are always preserved.

Options:
  --client auto|codex|claude|all  Target client. Default: auto.
  --dry-run                       Print actions without changing files.
  -h, --help                      Show this help.
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
  if [ -n "${CODEX_THREAD_ID:-}" ] || [ "${__CFBundleIdentifier:-}" = "com.openai.codex" ]; then
    printf 'codex'
    return
  fi
  if env | grep -Eq '^(CLAUDE|ANTHROPIC)'; then
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

uninstall_target() {
  skills_root="$1"
  target="$skills_root/twitter-digest"

  if [ ! -e "$target" ] && [ ! -L "$target" ]; then
    info "twitter-digest is not installed at $target"
    return
  fi

  backup_root="$skills_root/.backups"
  stamp="$(date +%Y%m%d-%H%M%S)"
  backup="$backup_root/twitter-digest-uninstalled-$stamp"
  suffix=1
  while [ -e "$backup" ] || [ -L "$backup" ]; do
    suffix=$((suffix + 1))
    backup="$backup_root/twitter-digest-uninstalled-$stamp-$suffix"
  done

  if [ "$DRY_RUN" = "1" ]; then
    info "Would move $target to $backup"
    return
  fi

  mkdir -p "$backup_root"
  mv "$target" "$backup"
  if [ -f "$backup/SKILL.md" ]; then
    mv "$backup/SKILL.md" "$backup/SKILL.md.disabled"
  fi
  info "Uninstalled twitter-digest from $target"
  info "Preserved the previous installation at $backup"
}

if [ "$CLIENT" = "auto" ]; then
  CLIENT="$(detect_client)"
fi

case "$CLIENT" in
  codex) uninstall_target "$HOME/.codex/skills" ;;
  claude) uninstall_target "$HOME/.claude/skills" ;;
  all)
    uninstall_target "$HOME/.codex/skills"
    uninstall_target "$HOME/.claude/skills"
    ;;
esac

printf 'Existing xurl authorization and Chat keys in ~/.xurl were preserved.\n'
