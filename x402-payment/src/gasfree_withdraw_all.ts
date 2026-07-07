#!/usr/bin/env node
import { TronWeb } from 'tronweb';
import { resolveWallet } from '@bankofai/agent-wallet';
import { createClientTronSigner } from '@bankofai/x402-tron';
import {
  assembleGasFreeTransaction,
  GasFreeAPIClient,
  GASFREE_API_BASE_URLS,
} from '@bankofai/x402-tron/gasfree';

const TRONWEB_READONLY_DUMMY_KEY = '0000000000000000000000000000000000000000000000000000000000000001';
const TRON_RPC_URLS: Record<string, string> = {
  mainnet: 'https://api.trongrid.io',
  nile: 'https://nile.trongrid.io',
  shasta: 'https://api.shasta.trongrid.io',
};

const NETWORK_IDS: Record<string, string> = {
  mainnet: 'tron:mainnet',
  nile: 'tron:nile',
  shasta: 'tron:shasta',
};

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

  const networkId = NETWORK_IDS[network] || network;
  const baseUrl = GASFREE_API_BASE_URLS[networkId];
  if (!baseUrl) {
    console.error(`Error: GasFree not supported on "${network}". Supported: mainnet, nile, shasta`);
    process.exit(1);
  }

  const tronWeb = new TronWeb({
    fullHost: TRON_RPC_URLS[network],
    privateKey: TRONWEB_READONLY_DUMMY_KEY,
  });

  const wallet = await resolveWallet({ network: networkId });
  const signer = await createClientTronSigner(wallet as any, {
    network: networkId,
    apiKey: process.env.TRON_GRID_API_KEY,
  });
  const userAddress = signer.address;
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

  const message = {
    token: tokenAddress,
    serviceProvider: provider.address,
    user: userAddress,
    receiver: toAddress,
    value: returnValue.toString(),
    maxFee: maxFee.toString(),
    deadline: deadline.toString(),
    version: '1',
    nonce: info.nonce.toString(),
  };
  const assembled = assembleGasFreeTransaction(message, networkId);
  const signature = await signer.signTypedData({
    domain: assembled.domain,
    types: assembled.types as unknown as Record<string, Array<{ name: string; type: string }>>,
    primaryType: assembled.primaryType,
    message: assembled.message,
  });

  console.error('[gasfree-withdraw] Submitting GasFree transaction...');
  const traceId = await gasFreeClient.submit(message, signature);
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
