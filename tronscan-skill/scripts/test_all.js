#!/usr/bin/env node
const { apiGet } = require('./utils');

const tests = [
  { name: 'search', fn: () => apiGet('search', { term: 'USDT', limit: 3 }), check: d => 'address' in d || 'token' in d },
  { name: 'account', fn: () => apiGet('account', { address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t' }), check: d => d.name === 'TetherToken' },
  { name: 'account --tokens', fn: () => apiGet('accountTokens', { address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t', limit: 3 }), check: d => Array.isArray(d.data) },
  { name: 'account --wallet', fn: () => apiGet('accountWallet', { address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t' }), check: d => Array.isArray(d.data) },
  { name: 'account --resources', fn: () => apiGet('accountResource', { address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t' }), check: d => 'total' in d || 'data' in d },
  { name: 'transaction --list', fn: () => apiGet('transaction', { sort: '-timestamp', limit: 1 }), check: d => d.data && d.data.length > 0 },
  { name: 'transaction --stats', fn: () => apiGet('transactionStats'), check: d => d.txCount > 0 },
  { name: 'token --list', fn: () => apiGet('tokensOverview', { filter: 'trc20', sort: 'marketcap', limit: 3 }), check: d => d.tokens && d.tokens.length > 0 },
  { name: 'token --trc20', fn: () => apiGet('tokenTrc20', { contract: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t' }), check: d => (d.trc20_tokens && d.trc20_tokens.length > 0) || d.name },
  { name: 'token --price', fn: () => apiGet('tokenPrice', { token: 'trx' }), check: d => d.price_in_usd !== undefined },
  { name: 'token --holders', fn: () => apiGet('tokenHoldersTrc20', { contract_address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t', limit: 3 }), check: d => (d.rangeTotal || d.total) > 0 },
  { name: 'block (latest)', fn: () => apiGet('block', { sort: '-number', limit: 1 }), check: d => d.data && d.data[0] && d.data[0].number > 0 },
  { name: 'block --stats', fn: () => apiGet('blockStats'), check: d => Object.keys(d).length > 0 },
  { name: 'contract', fn: () => apiGet('contract', { contract: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t' }), check: d => d.data && d.data.length > 0 },
  { name: 'contract --list', fn: () => apiGet('contracts', { sort: '-trxCount', limit: 3 }), check: d => (d.data && d.data.length > 0) || d.total > 0 },
  { name: 'transfer --trx', fn: () => apiGet('transferTrx', { address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t', limit: 2 }), check: d => 'data' in d || 'code' in d },
  { name: 'transfer --trc20', fn: () => apiGet('transferTrc20', { address: 'TKoJZgr58dCdwCv85deVgFkcrJPnBRiTio', trc20Id: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t', limit: 2 }), check: d => Array.isArray(d.data) },
  { name: 'transfer --trc10', fn: () => apiGet('transferTrc10', { address: 'TWd4WrZ9wn84f5x1hZhL4DHvk738ns5jwb', trc10Id: '1002000', limit: 2 }), check: d => Array.isArray(d.data) },
  { name: 'transfer --trc20-contract', fn: () => apiGet('trc20Transfers', { contract_address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t', limit: 2 }), check: d => (d.token_transfers && d.token_transfers.length > 0) || d.total > 0 },
  { name: 'overview (homepage)', fn: () => apiGet('homepage'), check: d => d.tps !== undefined },
  { name: 'overview --tps', fn: () => apiGet('tps'), check: d => d.data && d.data.currentTps > 0 },
  { name: 'overview --witnesses', fn: () => apiGet('witnesses', { limit: 3 }), check: d => (d.data && d.data.length > 0) || d.total > 0 },
  { name: 'overview --params', fn: () => apiGet('chainParams'), check: d => (d.tpiList && d.tpiList.length > 0) || Object.keys(d).length > 0 },
  { name: 'overview --funds', fn: () => apiGet('funds'), check: d => Object.keys(d).length > 0 },
  { name: 'security account', fn: () => apiGet('securityAccount', { address: 'TT2T17KZhoDu47i2E4FWxfG79zdkEWkU9N' }), check: d => ['send_ad_by_memo', 'has_fraud_transaction', 'fraud_token_creator', 'is_black_list'].every(k => typeof d[k] === 'boolean') },
  { name: 'security token', fn: () => apiGet('securityToken', { address: 'TPYmHEhy5n8TCEfYGqW2rPxsghSfzghPDn' }), check: d => d.token_level !== undefined && typeof d.has_url === 'boolean' },
  { name: 'security URL', fn: () => apiGet('securityUrl', { url: 'https://www.google.com.hk/' }), check: d => typeof d.cheat_url === 'boolean' },
  { name: 'security transaction', fn: () => apiGet('securityTransaction', { hashes: 'cfaad8dfd5c6842589fe6a4dafa810a50397ad58035639242dc02e53360e471b' }), check: d => d.cfaad8dfd5c6842589fe6a4dafa810a50397ad58035639242dc02e53360e471b !== undefined },
  { name: 'security multisig', fn: () => apiGet('securityMultisig', { address: 'THSiB9MT2sCnAUgnYs9euMCY9aiZCD4HB5' }), check: d => typeof d.multiSign === 'boolean' },
  { name: 'security approvals', fn: () => apiGet('securityApprovals', { address: 'THSiB9MT2sCnAUgnYs9euMCY9aiZCD4HB5' }), check: d => ['approveRiskContractCount', 'approveRiskAccountCount', 'approveRiskAddressCount'].every(k => d[k] !== undefined) },
];

(async () => {
  let pass = 0, fail = 0;
  for (const t of tests) {
    try {
      await new Promise(r => setTimeout(r, 220));
      const data = await t.fn();
      if (t.check(data)) {
        console.log('PASS  ' + t.name);
        pass++;
      } else {
        console.log('FAIL  ' + t.name + ' - unexpected response shape');
        fail++;
      }
    } catch (e) {
      console.log('FAIL  ' + t.name + ' - ' + e.message);
      fail++;
    }
  }
  console.log('\n=============================');
  console.log(pass + '/' + (pass + fail) + ' passed' + (fail ? ', ' + fail + ' FAILED' : ' - ALL GOOD'));
  process.exit(fail > 0 ? 1 : 0);
})();
