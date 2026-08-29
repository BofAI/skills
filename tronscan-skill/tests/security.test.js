const assert = require('assert');

const {
  assessAccount,
  assessApprovals,
  assessMultisig,
  assessToken,
  assessTransactions,
  assessUrl,
  isValidTronAddress,
  normalizeTargetUrl,
  requireTokenIdentifier,
  requireTransactionHashes,
} = require('../scripts/security');

let passed = 0;

function test(name, fn) {
  try {
    fn();
    passed++;
    console.log(`ok - ${name}`);
  } catch (error) {
    console.error(`not ok - ${name}`);
    throw error;
  }
}

test('validates TRON Base58Check addresses instead of checking the prefix only', () => {
  assert.equal(isValidTronAddress('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'), true);
  assert.equal(isValidTronAddress('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj61'), false);
  assert.equal(isValidTronAddress('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6u'), false);
});

test('accepts either a TRC10 id or a valid token contract address', () => {
  assert.equal(requireTokenIdentifier('1002000'), '1002000');
  assert.equal(requireTokenIdentifier('TPYmHEhy5n8TCEfYGqW2rPxsghSfzghPDn'), 'TPYmHEhy5n8TCEfYGqW2rPxsghSfzghPDn');
  assert.throws(() => requireTokenIdentifier('USDD'));
});

test('normalizes public URLs and removes query data before transmission', () => {
  const normalized = normalizeTargetUrl('example.com/app?token=secret#section');
  assert.equal(normalized.value, 'https://example.com/app');
  assert.equal(normalized.queryStripped, true);
  assert.throws(() => normalizeTargetUrl('ftp://example.com/file'));
  assert.throws(() => normalizeTargetUrl('https://user:password@example.com/'));
});

test('validates, lowercases, and deduplicates transaction hashes', () => {
  const first = 'A'.repeat(64);
  const second = 'b'.repeat(64);
  assert.deepEqual(requireTransactionHashes([`${first},${second}`, first]), [first.toLowerCase(), second]);
  assert.throws(() => requireTransactionHashes(['xyz']));
});

test('maps account risk booleans to review signals', () => {
  const result = assessAccount({
    send_ad_by_memo: false,
    has_fraud_transaction: true,
    fraud_token_creator: false,
    is_black_list: true,
  });
  assert.equal(result.status, 'review_required');
  assert.deepEqual(result.signals, ['has_fraud_transaction', 'is_black_list']);
});

test('does not treat an incomplete upstream response as a clean security result', () => {
  const account = assessAccount({ send_ad_by_memo: false });
  const token = assessToken({ token_level: '1' });
  const url = assessUrl({}, true);
  const multisig = assessMultisig({});
  const approvals = assessApprovals({ approveRiskContractCount: 0 });

  for (const result of [account, token, url, multisig, approvals]) {
    assert.equal(result.status, 'unknown');
    assert.equal(result.signals.length, 0);
    assert.equal(result.unknownReasons.length, 1);
  }
  assert.deepEqual(url.notes, ['Query parameters and fragments were removed before transmission.']);
});

test('treats token capabilities as review signals without declaring the token malicious', () => {
  const result = assessToken({
    token_level: '3',
    has_url: true,
    black_list_type: 1,
    increase_total_supply: 1,
    open_source: false,
    is_proxy: true,
  });
  assert.equal(result.status, 'review_required');
  assert(result.signals.includes('token_level_suspicious'));
  assert(result.signals.includes('proxy_contract'));
});

test('reports valid-looking transaction hashes that the API omits as unresolved', () => {
  const found = 'a'.repeat(64);
  const missing = 'b'.repeat(64);
  const result = assessTransactions({
    [found]: {
      riskToken: false,
      zeroTransfer: false,
      riskAddress: false,
      sameTailAttach: false,
      riskTransaction: false,
    },
  }, [found, missing]);
  assert.equal(result.status, 'unknown');
  assert.deepEqual(result.unresolved, [missing]);
});

test('detects unreachable and single-key multi-signature thresholds', () => {
  const result = assessMultisig({
    multiSign: true,
    ownerPermission: {
      threshold: 3,
      keys: [{ address: 'T1', weight: 1 }, { address: 'T2', weight: 1 }],
    },
    activePermissions: [{
      id: 2,
      threshold: 1,
      keys: [{ address: 'T1', weight: 1 }, { address: 'T2', weight: 1 }],
    }],
  });
  assert(result.signals.includes('owner_threshold_unreachable'));
  assert(result.signals.includes('active_2_single_key_can_authorize'));
});

test('handles missing active permissions and invalid weights without throwing', () => {
  const missing = assessMultisig({
    multiSign: true,
    ownerPermission: { threshold: 1, keys: [{ weight: 1 }] },
  });
  assert(missing.signals.includes('active_permissions_missing'));

  const invalidWeight = assessMultisig({
    multiSign: true,
    ownerPermission: { threshold: 1, keys: [{ weight: 0 }] },
    activePermissions: [],
  });
  assert(invalidWeight.signals.includes('owner_invalid_key_weight'));
  assert(invalidWeight.signals.includes('owner_threshold_unreachable'));
});

test('surfaces risk counters and unlimited risky approvals', () => {
  const result = assessApprovals({
    approveRiskContractCount: 1,
    approveRiskAccountCount: 0,
    approveRiskAddressCount: 1,
    riskApprove: [{
      unlimited: true,
      contract_address: 'TOKEN',
      to_address: 'SPENDER',
    }],
  });
  assert.equal(result.status, 'review_required');
  assert(result.signals.includes('approveRiskContractCount:1'));
  assert(result.signals.includes('unlimited_risky_approval:TOKEN:SPENDER'));
});

console.log(`${passed} tests passed`);
