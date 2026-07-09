#!/usr/bin/env node
import { TronWeb } from 'tronweb';
import { resolveWallet } from '@bankofai/agent-wallet';
import { createClientTronSigner } from '@bankofai/x402-tron';
import { GasFreeAPIClient, GASFREE_API_BASE_URLS } from '@bankofai/x402-tron/gasfree';
import {
  TRONWEB_READONLY_DUMMY_KEY,
  defaultTronTokenAddress,
  gasfreeDeadline,
  normalizeNetwork,
  signAndSubmitGasFree,
  tronRpcUrl,
} from './networks.js';

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
  const networkId = normalizeNetwork(network);
  const tokenAddress = options.token || defaultTronTokenAddress(networkId);
  const baseUrl = GASFREE_API_BASE_URLS[networkId];
  if (!baseUrl) {
    console.error(`Error: GasFree not supported on "${network}". Supported: mainnet, nile, shasta`);
    process.exit(1);
  }

  const tronWebOpts: Record<string, unknown> = {
    fullHost: tronRpcUrl(networkId),
    privateKey: TRONWEB_READONLY_DUMMY_KEY,
  };
  if (process.env.TRON_GRID_API_KEY) {
    tronWebOpts.headers = { 'TRON-PRO-API-KEY': process.env.TRON_GRID_API_KEY };
  }
  const tronWeb = new TronWeb(tronWebOpts as any);

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
  // The first transfer from an inactive account also pays the activation fee.
  const activateFee = info.active ? 0n : BigInt(asset.activateFee || 0);
  const maxFee = transferFee + activateFee;

  const contract = await tronWeb.contract().at(tokenAddress);
  const gfBalance = BigInt((await contract.methods.balanceOf(gasfreeAddress).call()).toString());
  const fmt = (v: bigint) => `${Number(v) / 10 ** decimals}`;

  console.error(`[gasfree-withdraw] GasFree balance: ${fmt(gfBalance)} token`);
  if (gfBalance <= maxFee) {
    console.error(`[gasfree-withdraw] Error: balance ${fmt(gfBalance)} <= maxFee ${fmt(maxFee)}`);
    process.exit(1);
  }

  const returnValue = gfBalance - maxFee;
  const deadline = gasfreeDeadline(networkId);

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
  console.error('[gasfree-withdraw] Submitting GasFree transaction...');
  const traceId = await signAndSubmitGasFree(signer, gasFreeClient, message, networkId);
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
