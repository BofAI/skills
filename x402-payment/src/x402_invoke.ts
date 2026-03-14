#!/usr/bin/env node
import { parseCliOptions, runCheck, runInvoke } from "./runtime.js";

async function main(): Promise<void> {
  const options = parseCliOptions(process.argv.slice(2));

  if (options.check === "true" || options.status === "true") {
    await runCheck();
    return;
  }

  await runInvoke(options);
}

await main();
