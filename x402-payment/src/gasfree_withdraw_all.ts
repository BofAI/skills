#!/usr/bin/env node
import { TronWeb } from 'tronweb';
import { GasFreeAPIClient, GASFREE_API_BASE_URLS, getChainId, TronClientSigner } from '@bankofai/x402';

const TRONWEB_READONLY_DUMMY_KEY = '0000000000000000000000000000000000000000000000000000000000000001';
GASFREE_API_BASE_URLS['tron:mainnet'] = 'https://tn-facilitator.bankofai.io/mainnet';
GASFREE_API_BASE_URLS['tron:nile'] = 'https://tn-facilitator.bankofai.io/nile';
GASFREE_API_BASE_URLS['tron:shasta'] = 'https://tn-facilitator.bankofai.io/shasta';

const TRON_RPC_URLS: Record<string, string> = {
  mainnet: 'https://api.trongrid.io',
  nile: 'https://nile.trongrid.io',
  shasta: 'https://api.shasta.trongrid.io',
};

function isTronAddress(address: string): boolean {
  return /^T[1-9A-HJ-NP-Za-km-z]{33}$/.test(address);
}

function tronAddressToEvmHex(tronWeb: any, address: string): string {
  if (!isTronAddress(address)) return address;
  const hex41 = String(tronWeb.address.toHex(address));
  return `0x${hex41.replace(/^41/i, '')}`;
}

function convertTronAddressesDeep(tronWeb: any, value: unknown): unknown {
  if (typeof value === 'string') {
    return isTronAddress(value) ? tronAddressToEvmHex(tronWeb, value) : value;
  }
  if (Array.isArray(value)) {
    return value.map((v) => convertTronAddressesDeep(tronWeb, v));
  }
  if (value && typeof value === 'object') {
    const next: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(value as Record<string, unknown>)) {
      next[key] = convertTronAddressesDeep(tronWeb, val);
    }
    return next;
  }
  return value;
}

async function main() {
  const args = process.argv.slice(2);
  const options: Record<string, string> = {};
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith('--')) {
      const key = arg.slice(2);
      const value = args[i + 1];
      if (value && !value.startsWith('--')) {
        options[key] = value;
        i++;
      } else {
        options[key] = 'true';
      }
    }
  }

  const network = options.network || 'nile';
  const tokenAddress = options.token || 'TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf';

  const baseUrl = GASFREE_API_BASE_URLS[`tron:${network}`];
  if (!baseUrl) {
    console.error(`Error: GasFree not supported on "${network}". Supported: mainnet, nile, shasta`);
    process.exit(1);
  }

  const tronWeb = new TronWeb({
    fullHost: TRON_RPC_URLS[network],
    privateKey: TRONWEB_READONLY_DUMMY_KEY,
  });

  const signer = await TronClientSigner.create();
  const userAddress = signer.getAddress();
  const toAddress = options.to || userAddress;
  const gasFreeClient = new GasFreeAPIClient(baseUrl);

  console.error(`[gasfree-withdraw] Network: ${network}, User: ${userAddress}`);
  const info = await gasFreeClient.getAddressInfo(userAddress);
  const gasfreeAddress = info.gasFreeAddress;
  if (!gasfreeAddress) {
    console.error(`Error: GasFree address not found for ${userAddress}`);
    process.exit(1);
  }

  console.error(`[gasfree-withdraw] GasFree address: ${gasfreeAddress}`);
  console.error(`[gasfree-withdraw] Active: ${info.active}, AllowSubmit: ${info.allowSubmit}, Nonce: ${info.nonce}`);
  if (!info.active && !info.allowSubmit) {
    console.error('[gasfree-withdraw] Error: Account not active and allowSubmit is false.');
    process.exit(1);
  }

  const asset = info.assets.find((a: any) => a.tokenAddress === tokenAddress);
  if (!asset) {
    console.error(`[gasfree-withdraw] Error: Token ${tokenAddress} not found in GasFree account`);
    process.exit(1);
  }

  const decimals = asset.decimal ?? 6;
  const transferFee = BigInt(asset.transferFee || 0);
  const maxFee = transferFee;

  const contract = await tronWeb.contract().at(tokenAddress);
  const gfBalance = BigInt((await contract.methods.balanceOf(gasfreeAddress).call()).toString());
  const fmt = (v: bigint) => `${Number(v) / 10 ** decimals}`;

  console.error(`[gasfree-withdraw] GasFree balance: ${fmt(gfBalance)} token`);
  if (gfBalance <= maxFee) {
    console.error(`[gasfree-withdraw] Error: balance ${fmt(gfBalance)} <= maxFee ${fmt(maxFee)}`);
    process.exit(1);
  }

  const returnValue = gfBalance - maxFee;
  const deadline = Math.floor(Date.now() / 1000) + 3600;

  const providers = await gasFreeClient.getProviders();
  if (!providers || providers.length === 0) {
    console.error('[gasfree-withdraw] Error: No GasFree service providers available');
    process.exit(1);
  }
  const provider = providers[0];
  console.error(`[gasfree-withdraw] Provider: ${provider.address} (${provider.name})`);

  const chainId = getChainId(`tron:${network}`);
  const { TronGasFree } = await import('@gasfree/gasfree-sdk');
  const gasFree = new TronGasFree({ chainId });

  const { domain, types, message } = gasFree.assembleGasFreeTransactionJson({
    token: tokenAddress,
    serviceProvider: provider.address,
    user: userAddress,
    receiver: toAddress,
    value: returnValue.toString(),
    maxFee: maxFee.toString(),
    deadline: deadline.toString(),
    version: '1',
    nonce: info.nonce.toString(),
  });

  const domainForSig = convertTronAddressesDeep(tronWeb, domain) as Record<string, unknown>;
  const messageForSig = convertTronAddressesDeep(tronWeb, message) as Record<string, unknown>;
  const signature = await signer.signTypedData(domainForSig, types, messageForSig, 'GasFreeTransaction');

  console.error('[gasfree-withdraw] Submitting GasFree transaction...');
  const traceId = await gasFreeClient.submit(domain, message, signature);
  console.error(`[gasfree-withdraw] Trace ID: ${traceId}`);
  console.error('[gasfree-withdraw] Waiting for completion...');

  const result = await gasFreeClient.waitForSuccess(traceId, 180000, 5000);

  process.stdout.write(JSON.stringify({
    status: result.state,
    traceId,
    to: toAddress,
    gasFreeAddress: gasfreeAddress,
    token: tokenAddress,
    amount: returnValue.toString(),
    maxFee: maxFee.toString(),
    txHash: result.txnHash || null,
  }, null, 2) + '\n');
}

main().catch((err) => {
  console.error(`[gasfree-withdraw] Error: ${err?.message || err}`);
  process.exit(1);
});
