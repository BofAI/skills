/**
 * Shared utilities for Multi-Sig & Account Permissions skill scripts.
 */

const { TronWeb } = require("tronweb");
const path = require("path");
const fs = require("fs");
const os = require("os");
const crypto = require("crypto");

const CONFIG = JSON.parse(
  fs.readFileSync(path.join(__dirname, "..", "resources", "permission_config.json"), "utf-8")
);

const TRX_DECIMALS = 6;

/* ---------- TronWeb factories ---------- */

function getTronWeb() {
  const network = (process.env.TRON_NETWORK || "mainnet").toLowerCase();
  const hosts = { mainnet: "https://api.trongrid.io", nile: "https://nile.trongrid.io", shasta: "https://api.shasta.trongrid.io" };
  const fullHost = hosts[network];
  if (!fullHost) throw new Error(`Unknown network "${network}".`);
  const privateKey = process.env.TRON_PRIVATE_KEY;
  if (!privateKey) throw new Error("TRON_PRIVATE_KEY environment variable is required");
  const opts = { fullHost, privateKey };
  if (process.env.TRONGRID_API_KEY) opts.headers = { "TRON-PRO-API-KEY": process.env.TRONGRID_API_KEY };
  return new TronWeb(opts);
}

function getTronWebReadOnly() {
  const network = (process.env.TRON_NETWORK || "mainnet").toLowerCase();
  const hosts = { mainnet: "https://api.trongrid.io", nile: "https://nile.trongrid.io", shasta: "https://api.shasta.trongrid.io" };
  const fullHost = hosts[network];
  if (!fullHost) throw new Error(`Unknown network "${network}".`);
  const opts = { fullHost };
  if (process.env.TRONGRID_API_KEY) opts.headers = { "TRON-PRO-API-KEY": process.env.TRONGRID_API_KEY };
  return new TronWeb(opts);
}

function getNetwork() {
  return (process.env.TRON_NETWORK || "mainnet").toLowerCase();
}

/* ---------- Account fetch helpers ---------- */

async function getAccountInfo(tronWeb, address) {
  const hexAddress = tronWeb.address.toHex(address);
  try {
    const account = await tronWeb.fullNode.request("wallet/getaccount", { address: hexAddress, visible: false }, "post");
    if (account && account.address) return account;
  } catch {}
  return tronWeb.trx.getAccount(address);
}

function normalizePermissionShape(account) {
  const owner = account.owner_permission || {};
  const active = (account.active_permission || []).map((perm) => ({
    id: perm.id,
    permission_name: perm.permission_name,
    threshold: perm.threshold,
    operations: perm.operations || "",
    keys: (perm.keys || []).map((key) => ({
      address: key.address,
      weight: key.weight || 1,
    })),
  }));
  return {
    owner: {
      threshold: owner.threshold,
      keys: (owner.keys || []).map((key) => ({
        address: key.address,
        weight: key.weight || 1,
      })),
    },
    active,
  };
}

function sameKeySet(left, right) {
  if (left.length !== right.length) return false;
  return left.every((item, index) =>
    item.address === right[index].address && (item.weight || 1) === (right[index].weight || 1)
  );
}

function permissionStateMatches(account, ownerPerm, activePerms) {
  const normalized = normalizePermissionShape(account);
  const expectedOwnerKeys = (ownerPerm.keys || []).map((key) => ({
    address: key.address,
    weight: key.weight || 1,
  }));
  const ownerMatches =
    (normalized.owner.threshold || 1) === (ownerPerm.threshold || 1) &&
    sameKeySet(normalized.owner.keys, expectedOwnerKeys);

  const expectedActives = (activePerms || []).map((perm) => ({
    id: perm.id,
    permission_name: perm.permission_name,
    threshold: perm.threshold,
    operations: perm.operations || "",
    keys: (perm.keys || []).map((key) => ({
      address: key.address,
      weight: key.weight || 1,
    })),
  }));

  const activeMatches =
    normalized.active.length === expectedActives.length &&
    normalized.active.every((perm, index) => {
      const expected = expectedActives[index];
      return perm.id === expected.id &&
        perm.permission_name === expected.permission_name &&
        (perm.threshold || 1) === (expected.threshold || 1) &&
        (perm.operations || "") === (expected.operations || "") &&
        sameKeySet(perm.keys, expected.keys);
    });

  return ownerMatches && activeMatches;
}

async function waitForPermissionSync(tronWeb, address, ownerPerm, activePerms, options = {}) {
  const attempts = options.attempts || 10;
  const delayMs = options.delayMs || 1500;
  for (let i = 0; i < attempts; i++) {
    const account = await getAccountInfo(tronWeb, address);
    if (account && account.address && permissionStateMatches(account, ownerPerm, activePerms)) {
      return { synced: true, attempts: i + 1 };
    }
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  return { synced: false, attempts };
}

/* ---------- Sun / TRX conversions ---------- */

function toSun(amount) {
  const parts = String(amount).split(".");
  const whole = parts[0] || "0";
  const frac = (parts[1] || "").slice(0, TRX_DECIMALS).padEnd(TRX_DECIMALS, "0");
  return BigInt(whole) * BigInt(10 ** TRX_DECIMALS) + BigInt(frac);
}

function fromSun(raw) {
  const str = String(raw).padStart(TRX_DECIMALS + 1, "0");
  const whole = str.slice(0, str.length - TRX_DECIMALS) || "0";
  const frac = str.slice(str.length - TRX_DECIMALS).replace(/0+$/, "");
  return frac ? `${whole}.${frac}` : whole;
}

/* ---------- Output helpers ---------- */

function outputJSON(data) { process.stdout.write(JSON.stringify(data, null, 2) + "\n"); }
function log(msg) { process.stderr.write(msg + "\n"); }

/* ---------- Operation bitmask helpers ---------- */

/**
 * Decode a hex-encoded operations bitmask into an array of operation names.
 * Bit N set means transaction type N is allowed.
 */
function decodeOperations(hexString) {
  if (!hexString) return [];
  const clean = hexString.replace(/^0x/i, "");
  const buf = Buffer.from(clean, "hex");
  const names = [];
  for (const [id, info] of Object.entries(CONFIG.operation_codes)) {
    const bitIndex = Number(id);
    const byteIndex = Math.floor(bitIndex / 8);
    const bitOffset = bitIndex % 8;
    if (byteIndex < buf.length && (buf[byteIndex] & (1 << bitOffset)) !== 0) {
      names.push(info.name);
    }
  }
  return names;
}

/**
 * Encode an array of operation names (or "all") into a hex bitmask string.
 */
function encodeOperations(operationNames) {
  const buf = Buffer.alloc(32, 0); // 256 bits
  if (operationNames === "all" || (Array.isArray(operationNames) && operationNames.includes("all"))) {
    // Use the canonical TRON active-permission "all ops" bitmask.
    // Computing this from permission_config.json is unsafe: the config is
    // an incomplete subset of TRON's operation registry, and including any
    // bit that is not on TRON's ALLOWED_ACTIVE_PERMISSION whitelist (e.g.
    // op 0 AccountCreateContract) causes the node to reject the transaction
    // with "operation[N] is invalid".
    return "7fff1fc0033efb0f000000000000000000000000000000000000000000000000";
  } else {
    // build name → id lookup
    const nameToId = {};
    for (const [id, info] of Object.entries(CONFIG.operation_codes)) {
      nameToId[info.name.toLowerCase()] = Number(id);
    }
    for (const name of operationNames) {
      const id = nameToId[name.toLowerCase()];
      if (id === undefined) throw new Error(`Unknown operation: "${name}". Available: ${Object.values(CONFIG.operation_codes).map(o => o.name).join(", ")}`);
      const byteIndex = Math.floor(id / 8);
      const bitOffset = id % 8;
      buf[byteIndex] |= (1 << bitOffset);
    }
  }
  return buf.toString("hex");
}

function getEnabledOperationBitCount(hexString) {
  if (!hexString) return 0;
  const clean = hexString.replace(/^0x/i, "");
  const buf = Buffer.from(clean, "hex");
  let count = 0;
  for (const byte of buf) {
    let value = byte;
    while (value) {
      value &= value - 1;
      count += 1;
    }
  }
  return count;
}

/* ---------- Security analysis ---------- */

/**
 * Classify account security level based on permission structure.
 * Returns { level, notes[] }
 */
function classifySecurity(ownerPerm, activePerms) {
  const notes = [];
  let level = "good";

  // Owner analysis
  const ownerKeys = (ownerPerm && ownerPerm.keys) || [];
  const ownerThreshold = (ownerPerm && ownerPerm.threshold) || 1;
  const ownerTotalWeight = ownerKeys.reduce((sum, k) => sum + (k.weight || 1), 0);
  const ownerIsMultisig = ownerThreshold > 1 || ownerKeys.length > 1;

  if (!ownerIsMultisig) {
    level = "critical";
    notes.push("Owner is single-key (no multi-sig protection)");
  } else if (ownerThreshold <= 1) {
    level = "weak";
    notes.push(`Owner has ${ownerKeys.length} keys but threshold is 1 — any single key has full control`);
  } else {
    notes.push(`Owner requires ${ownerThreshold}-of-${ownerKeys.length} signatures`);
  }

  // Active permission analysis
  if (activePerms && activePerms.length > 0) {
    for (const perm of activePerms) {
      const opsHex = perm.operations || "";
      const ops = opsHex ? decodeOperations(opsHex) : [];
      const enabledBits = getEnabledOperationBitCount(opsHex);
      const permName = perm.permission_name || `active:${perm.id}`;
      if (enabledBits === 0) {
        notes.push(`Active permission "${permName}" has no operations enabled`);
        if (level === "good") level = "moderate";
      } else if (ops.length === 0) {
        notes.push(`Active permission "${permName}" has ${enabledBits} enabled operation bit(s), but none are recognized by this skill`);
        if (level === "good") level = "moderate";
      } else if (ops.includes("TriggerSmartContract") && enabledBits === 1) {
        notes.push(`Active permission "${permName}" scoped to: TriggerSmartContract only`);
      } else if (ops.length >= Object.keys(CONFIG.operation_codes).length) {
        notes.push(`Active permission "${permName}" has all operations enabled`);
        if (level === "good") level = "moderate";
      } else {
        notes.push(`Active permission "${permName}" scoped to: ${ops.join(", ")}`);
        if (level === "moderate") level = "good";
      }
      const activeThreshold = perm.threshold || 1;
      const activeKeys = perm.keys || [];
      if (activeThreshold > 1) {
        notes.push(`Active "${permName}" requires ${activeThreshold}-of-${activeKeys.length}`);
      }
    }
  }

  // Upgrade to strong if owner is multi-sig with threshold >= 2 and active is scoped
  if (ownerThreshold >= 2 && level === "good") {
    const allScoped = (activePerms || []).every(p => {
      const opsHex = p.operations || "";
      const ops = opsHex ? decodeOperations(opsHex) : [];
      const enabledBits = getEnabledOperationBitCount(opsHex);
      return enabledBits > 0 && (ops.length > 0 || enabledBits === 1);
    });
    if (allScoped) level = "strong";
  }

  return { level, notes };
}

/* ---------- Proposal storage ---------- */

function getProposalDir(subdir) {
  const dir = path.join(os.homedir(), ".clawdbot", "multisig", subdir || "pending");
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function generateProposalId() {
  const ts = Math.floor(Date.now() / 1000);
  const rand = crypto.randomBytes(2).toString("hex");
  return `prop_${ts}_${rand}`;
}

function saveProposal(proposal) {
  const dir = getProposalDir("pending");
  const filePath = path.join(dir, `${proposal.proposalId}.json`);
  fs.writeFileSync(filePath, JSON.stringify(proposal, null, 2), "utf-8");
  return filePath;
}

function loadProposal(idOrPath) {
  // Try as direct file path
  if (fs.existsSync(idOrPath)) {
    return JSON.parse(fs.readFileSync(idOrPath, "utf-8"));
  }
  // Try in pending dir
  const pendingPath = path.join(getProposalDir("pending"), `${idOrPath}.json`);
  if (fs.existsSync(pendingPath)) {
    return JSON.parse(fs.readFileSync(pendingPath, "utf-8"));
  }
  throw new Error(`Proposal not found: "${idOrPath}". Check ~/.clawdbot/multisig/pending/`);
}

function archiveProposal(proposalId) {
  const srcDir = getProposalDir("pending");
  const dstDir = getProposalDir("executed");
  const srcPath = path.join(srcDir, `${proposalId}.json`);
  const dstPath = path.join(dstDir, `${proposalId}.json`);
  if (fs.existsSync(srcPath)) {
    fs.renameSync(srcPath, dstPath);
    return dstPath;
  }
  return null;
}

function listProposals() {
  const dir = getProposalDir("pending");
  const files = fs.readdirSync(dir).filter(f => f.endsWith(".json"));
  return files.map(f => JSON.parse(fs.readFileSync(path.join(dir, f), "utf-8")));
}

/* ---------- Permission formatting ---------- */

function formatPermConfig(keys, threshold) {
  const total = keys.length;
  return `${threshold}-of-${total}`;
}

module.exports = {
  CONFIG,
  TRX_DECIMALS,
  getTronWeb,
  getTronWebReadOnly,
  getNetwork,
  getAccountInfo,
  waitForPermissionSync,
  toSun,
  fromSun,
  outputJSON,
  log,
  decodeOperations,
  encodeOperations,
  getEnabledOperationBitCount,
  classifySecurity,
  getProposalDir,
  generateProposalId,
  saveProposal,
  loadProposal,
  archiveProposal,
  listProposals,
  formatPermConfig,
};
