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
  X402_TS_REPO_ROOT="$REPO_ROOT/typescript/packages" node -e '
    const fs = require("fs");
    const path = require("path");
    const file = process.argv[1];
    const packagesRoot = process.env.X402_TS_REPO_ROOT;
    const packagePaths = [
      "core",
      "extensions",
      "http/fetch",
      "mechanisms/tron",
      "mechanisms/evm",
      "mcp",
    ];
    const versions = {};
    for (const relativePath of packagePaths) {
      const packageFile = path.join(packagesRoot, relativePath, "package.json");
      const manifest = JSON.parse(fs.readFileSync(packageFile, "utf8"));
      versions[manifest.name] = manifest.version;
    }
    const pkg = JSON.parse(fs.readFileSync(file, "utf8"));
    const patch = (deps) => {
      if (!deps) return;
      for (const [name, value] of Object.entries(deps)) {
        if (typeof value === "string" && value.startsWith("workspace:")) {
          deps[name] = versions[name] ?? value;
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
  find "$dst" -maxdepth 1 -name '*.tgz' -delete
  patch_workspace_versions "$dst/package.json"
  (cd "$dst" && npm pack >/dev/null)
}

echo "[bootstrap] Packing local SDK packages..."
pack_local_sdk "core" "core"
pack_local_sdk "extensions" "extensions"
pack_local_sdk "http/fetch" "fetch"
pack_local_sdk "mechanisms/tron" "tron"
pack_local_sdk "mechanisms/evm" "evm"
pack_local_sdk "mcp" "mcp"

echo "[bootstrap] Installing skill runtime dependencies..."
cd "$SKILL_DIR"
rm -rf node_modules
npm install --no-save --no-package-lock \
  tsx@^4.21.0 \
  typescript@^5.9.3 \
  "$TMP_DIR/stage/core"/*.tgz \
  "$TMP_DIR/stage/extensions"/*.tgz \
  "$TMP_DIR/stage/fetch"/*.tgz \
  "$TMP_DIR/stage/tron"/*.tgz \
  "$TMP_DIR/stage/evm"/*.tgz \
  "$TMP_DIR/stage/mcp"/*.tgz

echo "[bootstrap] Done. Local v2 SDK packages are installed into skills/x402-payment/node_modules."
