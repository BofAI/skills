#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../../x402" && pwd)"
PACKAGES_DIR="$REPO_ROOT/typescript/packages"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$TMP_DIR/stage"

patch_workspace_versions() {
  local package_json="$1"
  node -e '
    const fs = require("fs");
    const file = process.argv[1];
    const pkg = JSON.parse(fs.readFileSync(file, "utf8"));
    const patch = (deps) => {
      if (!deps) return;
      for (const [name, value] of Object.entries(deps)) {
        if (typeof value === "string") {
          deps[name] = value.replace(/workspace:\*/g, "2.6.0").replace(/workspace:~/g, "2.6.0");
        }
      }
    };
    patch(pkg.dependencies);
    patch(pkg.devDependencies);
    patch(pkg.peerDependencies);
    fs.writeFileSync(file, JSON.stringify(pkg, null, 2) + "\n");
  ' "$package_json"
}

pack_local_sdk() {
  local relative_path="$1"
  local alias_name="$2"
  local src="$PACKAGES_DIR/$relative_path"
  local dst="$TMP_DIR/stage/$alias_name"

  cp -R "$src" "$dst"
  patch_workspace_versions "$dst/package.json"
  (cd "$dst" && npm pack >/dev/null)
}

echo "[bootstrap] Packing local SDK packages..."
pack_local_sdk "core" "core"
pack_local_sdk "extensions" "extensions"
pack_local_sdk "http/fetch" "fetch"
pack_local_sdk "mechanisms/tron" "tron"
pack_local_sdk "mechanisms/evm" "evm"

echo "[bootstrap] Installing skill runtime dependencies..."
cd "$SKILL_DIR"
rm -rf node_modules
npm install --no-save --no-package-lock \
  tronweb@^6.0.0 \
  viem@^2.45.2 \
  tsx@^4.21.0 \
  typescript@^5.9.3 \
  "$TMP_DIR/stage/core"/*.tgz \
  "$TMP_DIR/stage/extensions"/*.tgz \
  "$TMP_DIR/stage/fetch"/*.tgz \
  "$TMP_DIR/stage/tron"/*.tgz \
  "$TMP_DIR/stage/evm"/*.tgz

echo "[bootstrap] Done. Local v2 SDK packages are installed into skills/x402-payment/node_modules."
