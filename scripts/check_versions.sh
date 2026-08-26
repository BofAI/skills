#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VERSION_FILE="$ROOT_DIR/VERSION"
CHANGELOG_FILE="$ROOT_DIR/CHANGELOG.md"
failures=0

fail() {
  printf 'version check: %s\n' "$1" >&2
  failures=$((failures + 1))
}

[ -f "$VERSION_FILE" ] || {
  printf 'version check: missing VERSION\n' >&2
  exit 1
}

release_version=$(sed -n '1p' "$VERSION_FILE")
line_count=$(wc -l < "$VERSION_FILE" | tr -d ' ')

if [ "$line_count" -ne 1 ]; then
  fail "VERSION must contain exactly one line"
fi

if ! printf '%s\n' "$release_version" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$'; then
  fail "invalid VERSION value: $release_version"
fi

for skill_file in "$ROOT_DIR"/*/SKILL.md; do
  skill_version=$(awk '
    NR == 1 && $0 == "---" { in_frontmatter = 1; next }
    in_frontmatter && $0 == "---" { exit }
    in_frontmatter && $1 == "version:" {
      sub(/^[[:space:]]*version:[[:space:]]*/, "")
      print
      exit
    }
  ' "$skill_file" | tr -d "\"'")

  relative_path=${skill_file#"$ROOT_DIR"/}
  if [ -z "$skill_version" ]; then
    fail "$relative_path has no frontmatter version"
  elif [ "$skill_version" != "$release_version" ]; then
    fail "$relative_path has $skill_version, expected $release_version"
  fi
done

for package_file in "$ROOT_DIR"/*/package.json; do
  [ -e "$package_file" ] || continue
  package_version=$(node -e '
    const data = require(process.argv[1]);
    process.stdout.write(data.version || "");
  ' "$package_file")

  relative_path=${package_file#"$ROOT_DIR"/}
  if [ -n "$package_version" ] && [ "$package_version" != "$release_version" ]; then
    fail "$relative_path has $package_version, expected $release_version"
  fi
done

changelog_version=$(sed -n 's/^## \[\([^]]*\)\].*/\1/p' "$CHANGELOG_FILE" | sed -n '1p')
if [ "$changelog_version" != "$release_version" ]; then
  fail "CHANGELOG.md starts with ${changelog_version:-no version}, expected $release_version"
fi

if [ "${GITHUB_REF_TYPE:-}" = "tag" ] && [ "${GITHUB_REF_NAME:-}" != "v$release_version" ]; then
  fail "release tag ${GITHUB_REF_NAME:-missing} does not match v$release_version"
fi

if [ "$failures" -ne 0 ]; then
  exit 1
fi

printf 'All skill versions match %s.\n' "$release_version"
