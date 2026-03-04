const axios = require('axios');
const path = require('path');

const config = require(path.join(__dirname, '..', 'resources', 'api_config.json'));
const commonTokens = require(path.join(__dirname, '..', 'resources', 'common_tokens.json'));

const API_KEY = process.env.TRONSCAN_API_KEY;
if (!API_KEY) {
  console.error('[tronscan] ERROR: TRONSCAN_API_KEY environment variable is not set.');
  console.error('[tronscan] Get a free key at https://tronscan.org/#/myaccount/apiKeys');
  process.exit(1);
}

const client = axios.create({
  baseURL: config.baseUrl,
  headers: { 'TRON-PRO-API-KEY': API_KEY },
  timeout: 15000,
});

function log(...args) {
  console.error('[tronscan]', ...args);
}

function output(data) {
  console.log(JSON.stringify(data, null, 2));
}

function fatal(message) {
  log('ERROR:', message);
  output({ error: message });
  process.exit(1);
}

async function apiGet(endpointKey, params = {}) {
  const url = config.endpoints[endpointKey];
  if (!url) fatal(`Unknown endpoint key: ${endpointKey}`);
  log(`GET ${url}`, params);
  const res = await client.get(url, { params });
  return res.data;
}

async function apiGetRaw(urlPath, params = {}) {
  log(`GET ${urlPath}`, params);
  const res = await client.get(urlPath, { params });
  return res.data;
}

function parseArgs(argv) {
  const args = {};
  const positional = [];
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg.startsWith('--')) {
      const key = arg.slice(2);
      const next = argv[i + 1];
      if (next && !next.startsWith('--')) {
        args[key] = next;
        i++;
      } else {
        args[key] = true;
      }
    } else {
      positional.push(arg);
    }
  }
  return { args, positional };
}

function formatTrx(sunAmount) {
  return (Number(sunAmount) / 1e6).toFixed(6);
}

function formatTimestamp(ms) {
  return new Date(Number(ms)).toISOString();
}

function resolveToken(symbolOrAddress, network = 'mainnet') {
  const tokens = commonTokens[network] || commonTokens.mainnet;
  const upper = (symbolOrAddress || '').toUpperCase();
  if (tokens[upper]) return tokens[upper];
  for (const t of Object.values(tokens)) {
    if (t.address === symbolOrAddress) return t;
  }
  return null;
}

module.exports = {
  config,
  commonTokens,
  client,
  log,
  output,
  fatal,
  apiGet,
  apiGetRaw,
  parseArgs,
  formatTrx,
  formatTimestamp,
  resolveToken,
  API_KEY,
};
