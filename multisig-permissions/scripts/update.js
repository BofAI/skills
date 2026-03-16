#!/usr/bin/env node

/**
 * update.js — Modify account permissions (owner, active, witness).
 *
 * ⚠️  THIS IS THE MOST DANGEROUS SCRIPT IN THE REPO.
 * Misconfiguring owner permissions can permanently lock an account.
 *
 * Usage:
 *   node update.js add-key <address> [--permission owner|active] [--weight 1] [--dry-run]
 *   node update.js remove-key <address> [--permission owner|active] [--dry-run]
 *   node update.js set-threshold <number> [--permission owner|active] [--dry-run]
 *   node update.js scope-active [--id 2] [--operations Op1,Op2,...] [--dry-run]
 *   node update.js from-template <template> [--key1 addr] [--key2 addr] [--key3 addr] [--key4 addr] [--key5 addr] [--dry-run]
 *
 * Examples:
 *   node update.js add-key TNewKey... --permission owner --weight 1 --dry-run
 *   node update.js set-threshold 2 --permission owner --dry-run
 *   node update.js scope-active --id 2 --operations TriggerSmartContract,TransferContract --dry-run
 *   node update.js from-template agent-restricted --key1 THuman... --key2 TBackup... --key3 TAgent... --dry-run
 */

const { TronWeb } = require("tronweb");
const {
  CONFIG, getTronWeb, encodeOperations, decodeOperations,
  classifySecurity, formatPermConfig, outputJSON, log,
} = require("./utils");

function toBase58(addr) {
  try { return TronWeb.address.fromHex(addr); } catch { return addr; }
}

function parseArgs() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error("Usage: node update.js <action> [args] [--options]");
    console.error("Actions: add-key, remove-key, set-threshold, scope-active, from-template");
    process.exit(1);
  }

  const action = args[0];
  const positional = args[1] && !args[1].startsWith("--") ? args[1] : null;
  const flags = {};

  for (let i = 1; i < args.length; i++) {
    if (args[i] === "--dry-run") { flags.dryRun = true; continue; }
    if (args[i] === "--permission" && args[i + 1]) { flags.permission = args[++i]; continue; }
    if (args[i] === "--weight" && args[i + 1]) { flags.weight = Number(args[++i]); continue; }
    if (args[i] === "--id" && args[i + 1]) { flags.activeId = Number(args[++i]); continue; }
    if (args[i] === "--operations" && args[i + 1]) { flags.operations = args[++i].split(","); continue; }
    if (args[i] === "--threshold" && args[i + 1]) { flags.threshold = Number(args[++i]); continue; }
    if (/^--key\d+$/.test(args[i]) && args[i + 1]) {
      if (!flags.keys) flags.keys = {};
      flags.keys[args[i].replace("--", "")] = args[++i];
      continue;
    }
  }

  return { action, positional, ...flags };
}

function clonePerms(account) {
  const owner = account.owner_permission
    ? JSON.parse(JSON.stringify(account.owner_permission))
    : { type: 0, permission_name: "owner", threshold: 1, keys: [{ address: account.address, weight: 1 }] };

  const actives = (account.active_permission || []).map(p => JSON.parse(JSON.stringify(p)));
  const witness = account.witness_permission ? JSON.parse(JSON.stringify(account.witness_permission)) : undefined;

  return { owner, actives, witness };
}

function findActive(actives, id) {
  const targetId = id || 2;
  const match = actives.find(p => p.id === targetId);
  if (!match) throw new Error(`Active permission with id=${targetId} not found. Available: ${actives.map(p => p.id).join(", ")}`);
  return match;
}

function validateThreshold(perm, label) {
  const totalWeight = perm.keys.reduce((s, k) => s + (k.weight || 1), 0);
  if (perm.threshold > totalWeight) {
    throw new Error(
      `LOCKOUT DANGER: ${label} threshold (${perm.threshold}) exceeds total key weight (${totalWeight}). ` +
      `This would permanently lock the account. Aborting.`
    );
  }
  if (perm.keys.length === 0) {
    throw new Error(`LOCKOUT DANGER: ${label} has no keys. This would permanently lock the account. Aborting.`);
  }
}

async function main() {
  const opts = parseArgs();
  const tronWeb = getTronWeb();
  const walletAddress = tronWeb.defaultAddress.base58;

  log(`Loading permissions for ${walletAddress} ...`);
  const account = await tronWeb.trx.getAccount(walletAddress);
  if (!account || !account.address) {
    outputJSON({ error: `Account not found or not activated: ${walletAddress}` });
    process.exit(1);
  }

  const { owner, actives, witness } = clonePerms(account);
  const dryRun = !!opts.dryRun;

  const result = {
    action: opts.action,
    wallet: walletAddress,
    dry_run: dryRun,
  };

  // ---- Apply the requested modification ----

  switch (opts.action) {
    case "add-key": {
      const keyAddr = opts.positional;
      if (!keyAddr) { outputJSON({ error: "Usage: node update.js add-key <address> [--permission owner|active] [--weight 1]" }); process.exit(1); }
      const weight = opts.weight || 1;
      const target = opts.permission === "active" ? findActive(actives, opts.activeId) : owner;
      const label = opts.permission === "active" ? `active:${target.id}` : "owner";

      if (target.keys.some(k => k.address === keyAddr)) {
        outputJSON({ error: `Key ${keyAddr} already exists in ${label} permission` });
        process.exit(1);
      }

      target.keys.push({ address: keyAddr, weight });
      result.added_key = { address: keyAddr, weight, permission: label };
      log(`Adding key ${keyAddr} (weight ${weight}) to ${label} ...`);
      break;
    }

    case "remove-key": {
      const keyAddr = opts.positional;
      if (!keyAddr) { outputJSON({ error: "Usage: node update.js remove-key <address> [--permission owner|active]" }); process.exit(1); }
      const target = opts.permission === "active" ? findActive(actives, opts.activeId) : owner;
      const label = opts.permission === "active" ? `active:${target.id}` : "owner";

      const idx = target.keys.findIndex(k => k.address === keyAddr);
      if (idx === -1) {
        outputJSON({ error: `Key ${keyAddr} not found in ${label} permission` });
        process.exit(1);
      }

      if (keyAddr === walletAddress) {
        log(`⚠️  WARNING: You are removing YOUR OWN key from ${label} permission!`);
        result.warning = "Removing caller's own key";
      }

      target.keys.splice(idx, 1);
      result.removed_key = { address: keyAddr, permission: label };
      log(`Removing key ${keyAddr} from ${label} ...`);
      break;
    }

    case "set-threshold": {
      const threshold = opts.positional ? Number(opts.positional) : opts.threshold;
      if (!threshold || threshold < 1) { outputJSON({ error: "Usage: node update.js set-threshold <number> [--permission owner|active]" }); process.exit(1); }
      const target = opts.permission === "active" ? findActive(actives, opts.activeId) : owner;
      const label = opts.permission === "active" ? `active:${target.id}` : "owner";

      result.previous_threshold = target.threshold;
      target.threshold = threshold;
      result.new_threshold = threshold;
      result.permission = label;
      log(`Setting ${label} threshold to ${threshold} ...`);
      break;
    }

    case "scope-active": {
      const active = findActive(actives, opts.activeId);
      if (!opts.operations || opts.operations.length === 0) {
        outputJSON({ error: "Usage: node update.js scope-active --operations Op1,Op2,... [--id 2]" });
        process.exit(1);
      }
      const oldOps = decodeOperations(active.operations);
      const newOpsHex = encodeOperations(opts.operations);
      active.operations = newOpsHex;
      result.active_id = active.id;
      result.previous_operations = oldOps;
      result.new_operations = opts.operations;
      log(`Scoping active:${active.id} to [${opts.operations.join(", ")}] ...`);
      break;
    }

    case "from-template": {
      const templateName = opts.positional;
      if (!templateName || !CONFIG.templates[templateName]) {
        outputJSON({ error: `Unknown template: "${templateName}". Available: ${Object.keys(CONFIG.templates).join(", ")}` });
        process.exit(1);
      }
      const template = CONFIG.templates[templateName];
      const keyMap = opts.keys || {};

      // Deduplicated ordered list of all roles across owner + active permissions
      const allRoles = [...new Set([...template.owner.key_roles, ...template.active.flatMap(a => a.key_roles)])];

      // Resolve key roles to addresses via --roleName or positional --keyN
      function resolveRole(role) {
        // check exact role name match (e.g. --agent_key)
        for (const [flag, addr] of Object.entries(keyMap)) {
          if (flag === role.toLowerCase()) return addr;
        }
        // try positional: key1 = first role, key2 = second, etc.
        const roleIndex = allRoles.indexOf(role);
        if (roleIndex === -1) throw new Error(`Role "${role}" not found in template "${templateName}".`);
        const posFlag = `key${roleIndex + 1}`;
        if (keyMap[posFlag]) return keyMap[posFlag];
        throw new Error(`Missing address for role "${role}". Provide --key${roleIndex + 1} <address>`);
      }

      // Build owner
      owner.threshold = template.owner.threshold;
      owner.keys = template.owner.key_roles.map((role, i) => ({
        address: resolveRole(role),
        weight: template.owner.weights[i],
      }));

      actives.length = 0; // clear existing
      for (let i = 0; i < template.active.length; i++) {
        const tpl = template.active[i];
        const activePerm = {
          type: 2,
          id: i + 2,
          permission_name: tpl.name,
          threshold: tpl.threshold,
          keys: tpl.key_roles.map((role, j) => ({
            address: resolveRole(role),
            weight: tpl.weights[j],
          })),
          operations: encodeOperations(tpl.operations),
        };
        actives.push(activePerm);
      }

      result.template = templateName;
      result.description = template.description;
      log(`Applying template "${templateName}": ${template.description} ...`);
      break;
    }

    default:
      outputJSON({ error: `Unknown action: "${opts.action}". Use: add-key, remove-key, set-threshold, scope-active, from-template` });
      process.exit(1);
  }

  // ---- Validate the new config ----
  validateThreshold(owner, "Owner");
  for (const a of actives) {
    validateThreshold(a, `Active:${a.id}`);
  }

  const { level: newLevel, notes: newNotes } = classifySecurity(owner, actives);

  result.proposed_owner = {
    threshold: owner.threshold,
    keys: owner.keys.map(k => ({ address: toBase58(k.address), weight: k.weight })),
    config: formatPermConfig(owner.keys, owner.threshold),
  };
  result.proposed_active = actives.map(a => ({
    id: a.id,
    name: a.permission_name,
    threshold: a.threshold,
    keys: a.keys.map(k => ({ address: toBase58(k.address), weight: k.weight })),
    config: formatPermConfig(a.keys, a.threshold),
    operations: decodeOperations(a.operations),
  }));
  result.security_level = newLevel;
  result.analysis = newNotes;

  if (dryRun) {
    result.status = "dry_run";
    log("⚠️  DRY RUN — no transaction sent. Review proposed config above.");
    outputJSON(result);
    return;
  }

  // ---- Warn for owner changes ----
  if (opts.action !== "scope-active" && (opts.permission !== "active")) {
    log("⚠️  WARNING: Modifying owner permissions. This is irreversible if misconfigured.");
  }

  // ---- Build and send the permission update transaction ----
  try {
    // Format for TronWeb API
    const ownerFormatted = {
      type: 0,
      permission_name: "owner",
      threshold: owner.threshold,
      keys: owner.keys.map(k => ({
        address: tronWeb.address.toHex(k.address),
        weight: k.weight,
      })),
    };

    const activesFormatted = actives.map(a => ({
      type: 2,
      id: a.id,
      permission_name: a.permission_name || "active",
      threshold: a.threshold,
      operations: a.operations,
      keys: a.keys.map(k => ({
        address: tronWeb.address.toHex(k.address),
        weight: k.weight,
      })),
    }));

    const witnessFormatted = witness ? {
      type: 1,
      permission_name: witness.permission_name || "witness",
      threshold: witness.threshold || 1,
      keys: (witness.keys || []).map(k => ({
        address: tronWeb.address.toHex(k.address),
        weight: k.weight || 1,
      })),
    } : undefined;

    const tx = await tronWeb.transactionBuilder.updateAccountPermissions(
      tronWeb.address.toHex(walletAddress),
      ownerFormatted,
      witnessFormatted,
      activesFormatted
    );

    const signed = await tronWeb.trx.sign(tx);
    const broadcast = await tronWeb.trx.sendRawTransaction(signed);

    result.status = broadcast.result ? "submitted" : "failed";
    result.tx_id = broadcast.txid;
    log(`Transaction: ${broadcast.txid}`);
  } catch (e) {
    result.status = "failed";
    result.error = e.message || String(e);
  }

  outputJSON(result);
}

main().catch((e) => { outputJSON({ error: e.message }); process.exit(1); });
