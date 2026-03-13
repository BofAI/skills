#!/usr/bin/env node
import { parseCliOptions, runBalance, runCheck, runInvoke } from "./runtime.js";

function printHelp(): void {
  process.stdout.write(
    [
      "x402 CLI",
      "",
      "Usage:",
      "  x402 status",
      "  x402 balance",
      "  x402 pay <url> [-X <method>] [-d <json>] [-q <params>] [-h <json>]",
      "           [--network <network>] [--asset <asset>] [--pair <pair>]",
      "           [--max-amount <atomic-units>] [--correlation-id <id>] [--json]",
      "",
      "Notes:",
      "  - `check` and `invoke` remain available as compatibility aliases.",
      "  - Selection priority is: network + pair/asset, then network, then first available option.",
    ].join("\n") + "\n",
  );
}

async function main(): Promise<void> {
  const argv = process.argv.slice(2);
  const [command, ...rest] = argv;

  if (!command || command === "help" || command === "--help" || command === "-h") {
    printHelp();
    return;
  }

  if (command === "check" || command === "status") {
    await runCheck();
    return;
  }

  if (command === "balance") {
    await runBalance();
    return;
  }

  if (command === "pay" || command === "invoke") {
    await runInvoke(parseCliOptions(rest));
    return;
  }

  if (command.startsWith("--")) {
    await runInvoke(parseCliOptions(argv));
    return;
  }

  throw new Error(`Unknown command: ${command}`);
}

try {
  await main();
} catch (error) {
  const message = error instanceof Error ? error.message : "Unknown error";
  process.stderr.write(`${message}\n`);
  process.exit(1);
}
