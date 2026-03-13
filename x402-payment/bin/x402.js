#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const cliPath = path.resolve(__dirname, "../src/cli.ts");
const tsxLoaderPath = path.resolve(__dirname, "../node_modules/tsx/dist/loader.mjs");

const result = spawnSync(process.execPath, ["--import", tsxLoaderPath, cliPath, ...process.argv.slice(2)], {
  stdio: "inherit",
  env: process.env,
  cwd: path.resolve(__dirname, ".."),
});

if (result.error) {
  throw result.error;
}

process.exit(result.status ?? 0);
