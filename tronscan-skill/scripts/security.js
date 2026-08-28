#!/usr/bin/env node
/**
 * security.js - Read-only TronScan security checks with strict local validation
 *
 * Usage:
 *   node scripts/security.js account <address>
 *   node scripts/security.js token <token-id-or-contract>
 *   node scripts/security.js url <public-url>
 *   node scripts/security.js transaction <hash> [hash ...]
 *   node scripts/security.js multisig <address>
 *   node scripts/security.js approvals <address>
 */

const crypto = require('crypto');
const { apiGet, output, fatal, parseArgs, log } = require('./utils');

const BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
const TX_HASH_RE = /^[0-9a-f]{64}$/i;
const TRC10_ID_RE = /^\d+$/;
const MAX_TRANSACTION_HASHES = 20;
const CAVEAT = 'TronScan signals are one data source, not proof that a target is safe.';

const MODE_ALIASES = {
  auth: 'approvals',
  approval: 'approvals',
  approvals: 'approvals',
  account: 'account',
  token: 'token',
  url: 'url',
  transaction: 'transaction',
  tx: 'transaction',
  multisig: 'multisig',
  'multi-sig': 'multisig',
};

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest();
}

function decodeBase58(value) {
  let number = 0n;
  for (const character of value) {
    const index = BASE58_ALPHABET.indexOf(character);
    if (index === -1) return null;
    number = number * 58n + BigInt(index);
  }

  let decoded = Buffer.alloc(0);
  if (number !== 0n) {
    let hex = number.toString(16);
    if (hex.length % 2 !== 0) hex = `0${hex}`;
    decoded = Buffer.from(hex, 'hex');
  }

  let leadingZeroes = 0;
  while (leadingZeroes < value.length && value[leadingZeroes] === '1') leadingZeroes++;
  return Buffer.concat([Buffer.alloc(leadingZeroes), decoded]);
}

function isValidTronAddress(value) {
  if (typeof value !== 'string' || value.length !== 34 || !value.startsWith('T')) return false;
  const decoded = decodeBase58(value);
  if (!decoded || decoded.length !== 25 || decoded[0] !== 0x41) return false;

  const payload = decoded.subarray(0, 21);
  const expectedChecksum = sha256(sha256(payload)).subarray(0, 4);
  return crypto.timingSafeEqual(decoded.subarray(21), expectedChecksum);
}

function requireTronAddress(value, label = 'address') {
  const trimmed = String(value || '').trim();
  if (!isValidTronAddress(trimmed)) {
    throw new Error(`Invalid TRON ${label}: expected a Base58Check address beginning with T`);
  }
  return trimmed;
}

function requireTokenIdentifier(value) {
  const trimmed = String(value || '').trim();
  if (TRC10_ID_RE.test(trimmed)) return trimmed;
  return requireTronAddress(trimmed, 'token contract address');
}

function normalizeTargetUrl(value) {
  const trimmed = String(value || '').trim();
  if (!trimmed) throw new Error('Missing URL');

  const candidate = /^[a-z][a-z\d+.-]*:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
  let parsed;
  try {
    parsed = new URL(candidate);
  } catch {
    throw new Error('Invalid URL');
  }

  if (!['http:', 'https:'].includes(parsed.protocol) || !parsed.hostname) {
    throw new Error('URL must use http or https and include a hostname');
  }
  if (parsed.username || parsed.password) {
    throw new Error('URL credentials must not be sent to the security service');
  }

  const queryStripped = Boolean(parsed.search || parsed.hash);
  parsed.search = '';
  parsed.hash = '';
  return { value: parsed.toString(), queryStripped };
}

function requireTransactionHashes(values) {
  const hashes = values
    .flatMap(value => String(value).split(','))
    .map(value => value.trim().toLowerCase())
    .filter(Boolean);

  if (hashes.length === 0) throw new Error('At least one transaction hash is required');
  if (hashes.length > MAX_TRANSACTION_HASHES) {
    throw new Error(`At most ${MAX_TRANSACTION_HASHES} transaction hashes may be checked at once`);
  }

  const invalid = hashes.filter(hash => !TX_HASH_RE.test(hash));
  if (invalid.length > 0) throw new Error('Every transaction hash must contain exactly 64 hexadecimal characters');
  return [...new Set(hashes)];
}

function statusFor(signals, unresolved = []) {
  if (signals.length > 0) return 'review_required';
  if (unresolved.length > 0) return 'unknown';
  return 'no_known_flags';
}

function hasAllOwnFields(data, fields) {
  return Boolean(
    data
    && typeof data === 'object'
    && fields.every(field => Object.prototype.hasOwnProperty.call(data, field)),
  );
}

function unknownAssessment(reason, extra = {}) {
  return {
    status: 'unknown',
    signals: [],
    unknownReasons: [reason],
    caveat: CAVEAT,
    ...extra,
  };
}

function assessAccount(data) {
  const fields = ['send_ad_by_memo', 'has_fraud_transaction', 'fraud_token_creator', 'is_black_list'];
  if (!hasAllOwnFields(data, fields)) {
    return unknownAssessment('upstream_response_missing_account_security_fields');
  }
  const signals = fields.filter(field => data?.[field] === true);
  return { status: statusFor(signals), signals, caveat: CAVEAT };
}

function assessToken(data) {
  const expectedFields = [
    'token_level',
    'has_url',
    'black_list_type',
    'increase_total_supply',
    'open_source',
    'is_proxy',
  ];
  if (!hasAllOwnFields(data, expectedFields)) {
    return unknownAssessment('upstream_response_missing_token_security_fields');
  }

  const signals = [];
  if (String(data?.token_level) === '3') signals.push('token_level_suspicious');
  if (String(data?.token_level) === '4') signals.push('token_level_unsafe');
  if (data?.has_url === true) signals.push('name_or_symbol_contains_url');
  if (Number(data?.black_list_type) === 1) signals.push('blacklist_capability');
  if (Number(data?.increase_total_supply) === 1) signals.push('supply_can_increase');
  if (data?.open_source === false) signals.push('contract_not_open_source');
  if (data?.is_proxy === true) signals.push('proxy_contract');
  return { status: statusFor(signals), signals, caveat: CAVEAT };
}

function assessUrl(data, queryStripped) {
  const notes = queryStripped
    ? ['Query parameters and fragments were removed before transmission.']
    : [];
  if (!hasAllOwnFields(data, ['cheat_url'])) {
    return unknownAssessment('upstream_response_missing_url_security_field', notes.length ? { notes } : {});
  }

  const signals = data?.cheat_url === true ? ['flagged_url'] : [];
  const assessment = { status: statusFor(signals), signals, caveat: CAVEAT };
  if (notes.length) assessment.notes = notes;
  return assessment;
}

function assessTransactions(data, requestedHashes) {
  const records = data && typeof data === 'object' && !Array.isArray(data) ? data : {};
  const normalizedRecords = new Map(Object.entries(records).map(([hash, value]) => [hash.toLowerCase(), value]));
  const unresolved = requestedHashes.filter(hash => !normalizedRecords.has(hash));
  const signals = [];

  for (const hash of requestedHashes) {
    const record = normalizedRecords.get(hash);
    if (!record) continue;
    for (const field of ['riskToken', 'zeroTransfer', 'riskAddress', 'sameTailAttach', 'riskTransaction']) {
      if (record[field] === true) signals.push(`${hash}:${field}`);
    }
  }

  return { status: statusFor(signals, unresolved), signals, unresolved, caveat: CAVEAT };
}

function permissionSignals(permission, prefix) {
  if (!permission || !Array.isArray(permission.keys)) return [`${prefix}_permission_missing`];
  const threshold = Number(permission.threshold);
  const rawWeights = permission.keys.map(key => Number(key.weight));
  const weights = rawWeights.filter(weight => Number.isFinite(weight) && weight > 0);
  const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);
  const signals = [];

  if (rawWeights.some(weight => !Number.isFinite(weight) || weight <= 0)) {
    signals.push(`${prefix}_invalid_key_weight`);
  }
  if (!Number.isFinite(threshold) || threshold <= 0) {
    signals.push(`${prefix}_invalid_threshold`);
  } else {
    if (totalWeight < threshold) signals.push(`${prefix}_threshold_unreachable`);
    if (weights.some(weight => weight >= threshold)) signals.push(`${prefix}_single_key_can_authorize`);
  }
  return signals;
}

function assessMultisig(data) {
  if (!hasAllOwnFields(data, ['multiSign'])) {
    return unknownAssessment('upstream_response_missing_multisig_status');
  }
  if (data?.multiSign !== true) {
    return { status: 'no_known_flags', signals: [], observations: ['multi_signature_not_enabled'], caveat: CAVEAT };
  }

  const signals = permissionSignals(data.ownerPermission, 'owner');
  if (!Array.isArray(data.activePermissions)) {
    signals.push('active_permissions_missing');
  } else {
    for (const permission of data.activePermissions) {
      signals.push(...permissionSignals(permission, `active_${permission.id ?? 'unknown'}`));
    }
  }

  return {
    status: statusFor(signals),
    signals,
    observations: ['multi_signature_enabled'],
    caveat: CAVEAT,
  };
}

function assessApprovals(data) {
  const countFields = [
    'approveRiskContractCount',
    'approveRiskAccountCount',
    'approveRiskAddressCount',
  ];
  if (!hasAllOwnFields(data, countFields)) {
    return unknownAssessment('upstream_response_missing_approval_security_fields');
  }

  const signals = countFields
    .filter(field => Number(data?.[field]) > 0)
    .map(field => `${field}:${data[field]}`);

  const riskApprovals = Array.isArray(data?.riskApprove) ? data.riskApprove : [];
  for (const approval of riskApprovals) {
    if (approval?.unlimited === true) {
      signals.push(`unlimited_risky_approval:${approval.contract_address}:${approval.to_address}`);
    }
  }
  return { status: statusFor(signals), signals, caveat: CAVEAT };
}

function assess(mode, data, context = {}) {
  if (mode === 'account') return assessAccount(data);
  if (mode === 'token') return assessToken(data);
  if (mode === 'url') return assessUrl(data, context.queryStripped);
  if (mode === 'transaction') return assessTransactions(data, context.hashes);
  if (mode === 'multisig') return assessMultisig(data);
  if (mode === 'approvals') return assessApprovals(data);
  throw new Error(`Unsupported security mode: ${mode}`);
}

function usage() {
  return [
    'Usage:',
    '  node scripts/security.js account <address>',
    '  node scripts/security.js token <token-id-or-contract>',
    '  node scripts/security.js url <public-url>',
    '  node scripts/security.js transaction <hash> [hash ...]',
    '  node scripts/security.js multisig <address>',
    '  node scripts/security.js approvals <address>',
  ].join('\n');
}

async function main() {
  const { positional } = parseArgs(process.argv);
  const mode = MODE_ALIASES[String(positional[0] || '').toLowerCase()];
  if (!mode) throw new Error(usage());

  let endpoint;
  let params;
  let subject;
  const context = {};

  if (mode === 'account' || mode === 'multisig' || mode === 'approvals') {
    subject = requireTronAddress(positional[1]);
    endpoint = { account: 'securityAccount', multisig: 'securityMultisig', approvals: 'securityApprovals' }[mode];
    params = { address: subject };
  } else if (mode === 'token') {
    subject = requireTokenIdentifier(positional[1]);
    endpoint = 'securityToken';
    params = { address: subject };
  } else if (mode === 'url') {
    const normalized = normalizeTargetUrl(positional[1]);
    subject = normalized.value;
    context.queryStripped = normalized.queryStripped;
    endpoint = 'securityUrl';
    params = { url: subject };
  } else {
    context.hashes = requireTransactionHashes(positional.slice(1));
    subject = context.hashes;
    endpoint = 'securityTransaction';
    params = { hashes: context.hashes.join(',') };
  }

  log(`Running ${mode} security check...`);
  const data = await apiGet(endpoint, params);
  output({
    query: { mode, subject },
    assessment: assess(mode, data, context),
    data,
  });
}

if (require.main === module) {
  main().catch(error => fatal(error.message));
}

module.exports = {
  assess,
  assessAccount,
  assessApprovals,
  assessMultisig,
  assessToken,
  assessTransactions,
  assessUrl,
  decodeBase58,
  isValidTronAddress,
  normalizeTargetUrl,
  permissionSignals,
  requireTokenIdentifier,
  requireTransactionHashes,
  requireTronAddress,
  unknownAssessment,
};
