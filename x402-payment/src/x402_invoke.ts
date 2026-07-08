#!/usr/bin/env node
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { x402Client, wrapFetchWithPayment } from '@bankofai/x402-fetch';
import { createClientTronSigner } from '@bankofai/x402-tron';
import { ExactTronScheme } from '@bankofai/x402-tron/exact/client';
import { registerExactGasFreeTronScheme } from '@bankofai/x402-tron/gasfree/client';
import { GasFreeAPIClient, GASFREE_API_BASE_URLS } from '@bankofai/x402-tron/gasfree';
import { createClientEvmSigner } from '@bankofai/x402-evm/adapters/agent-wallet';
import { ExactEvmScheme } from '@bankofai/x402-evm/exact/client';
import {
  TRONWEB_READONLY_DUMMY_KEY,
  TRON_NETWORKS,
  EVM_NETWORKS,
  normalizeNetwork,
  tronRpcUrl,
  evmRpcUrl,
  gasfreeDeadline,
  signAndSubmitGasFree,
} from './networks.js';

type WalletNetwork = 'tron' | 'eip155';

interface AgentWallet {
  getAddress(): Promise<string>;
  signMessage(msg: Uint8Array): Promise<string>;
  signTypedData(data: Record<string, unknown>): Promise<string>;
  signTransaction(payload: Record<string, unknown>): Promise<string>;
}

interface ResolvedWallet {
  wallet: AgentWallet;
  address: string;
}

function isTronAddress(address: string): boolean {
  return /^T[1-9A-HJ-NP-Za-km-z]{33}$/.test(address);
}

function isEvmAddress(address: string): boolean {
  return /^0x[0-9a-fA-F]{40}$/.test(address);
}

function normalizeHexSignature(signature: string): string {
  return signature.replace(/^0x/i, '');
}

function extractSignedTronTx(unsignedTx: Record<string, unknown>, signedResult: string): Record<string, unknown> {
  const trimmed = signedResult.trim();
  if (trimmed.startsWith('{')) {
    const parsed = JSON.parse(trimmed) as Record<string, unknown>;
    if (Array.isArray(parsed.signature)) {
      parsed.signature = parsed.signature.map((sig) =>
        typeof sig === 'string' ? normalizeHexSignature(sig) : sig,
      );
    }
    return parsed;
  }
  return {
    ...unsignedTx,
    signature: [normalizeHexSignature(signedResult)],
  };
}

// Used when we need the raw agent-wallet instance (e.g., TRON signTransaction in gasfree-activate).
// The resolved wallet is a network-agnostic credential source; agent-wallet resolves by chain
// family ('tron' / 'eip155'), and the target network is applied later when creating SDK signers.
async function resolveAgentWallet(network: WalletNetwork): Promise<ResolvedWallet | undefined> {
  try {
    const { resolveWallet } = await import('@bankofai/agent-wallet');
    const wallet = await resolveWallet({ network });
    const address = await wallet.getAddress();
    if (network === 'tron' && !isTronAddress(address)) return undefined;
    if (network === 'eip155' && !isEvmAddress(address)) return undefined;
    return { wallet: wallet as unknown as AgentWallet, address };
  } catch (err: any) {
    console.warn(`[x402] No ${network} agent-wallet resolved: ${err?.message || err}`);
    return undefined;
  }
}

async function findApiKey(): Promise<string | undefined> {
  if (process.env.TRON_GRID_API_KEY) return process.env.TRON_GRID_API_KEY;

  const configFiles = [
    path.join(process.cwd(), 'x402-config.json'),
    path.join(os.homedir(), '.x402-config.json')
  ];

  for (const file of configFiles) {
    if (fs.existsSync(file)) {
      try {
        const config = JSON.parse(fs.readFileSync(file, 'utf8'));
        const key = config.tron_grid_api_key || config.api_key;
        if (key) return key;
      } catch (e) { /* ignore */ }
    }
  }
  return undefined;
}

async function waitForTxConfirmation(tronWeb: any, txId: string, timeoutMs = 60000, intervalMs = 3000): Promise<boolean> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const info = await tronWeb.trx.getTransactionInfo(txId);
      if (info && info.id) return true;
    } catch (_) { /* not confirmed yet */ }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  return false;
}

async function handleGasFreeInfo(
  options: Record<string, string>,
  defaultWalletAddress: string | undefined,
): Promise<void> {
  let walletAddress: string;
  if (options['wallet']) {
    walletAddress = options['wallet'];
  } else if (defaultWalletAddress) {
    walletAddress = defaultWalletAddress;
  } else {
    console.error('Error: Provide --wallet <address> or configure a TRON agent-wallet account');
    process.exit(1);
  }

  const gasfreeNetwork = options.network || 'mainnet';
  const networkKey = normalizeNetwork(gasfreeNetwork);
  const baseUrl = (GASFREE_API_BASE_URLS as Record<string, string>)[networkKey];

  if (!baseUrl) {
    console.error(`Error: GasFree is not supported on network "${gasfreeNetwork}". Supported: mainnet, nile, shasta`);
    process.exit(1);
  }

  const gasFreeClient = new GasFreeAPIClient(baseUrl);
  console.error(`[gasfree] Querying GasFree info for ${walletAddress} on ${gasfreeNetwork}...`);

  try {
    const info = await gasFreeClient.getAddressInfo(walletAddress);
    const result = {
      network: gasfreeNetwork,
      accountAddress: info.accountAddress,
      gasFreeAddress: info.gasFreeAddress,
      active: info.active,
      allowSubmit: info.allowSubmit,
      nonce: info.nonce,
      assets: (info.assets || []).map((asset: any) => ({
        tokenSymbol: asset.tokenSymbol,
        tokenAddress: asset.tokenAddress,
        balance: asset.balance,
        frozen: asset.frozen,
        decimal: asset.decimal,
        activateFee: asset.activateFee,
        transferFee: asset.transferFee,
      })),
    };
    process.stdout.write(JSON.stringify(result, null, 2) + '\n');
  } catch (error: any) {
    console.error(`[gasfree] Error: ${error.message || 'Unknown error'}`);
    process.stdout.write(JSON.stringify({ error: error.message || 'Unknown error' }, null, 2) + '\n');
    process.exit(1);
  }
}

async function handleGasFreeActivate(
  options: Record<string, string>,
  deps: {
    tronWallet: AgentWallet;
    apiKey: string | undefined;
    TronWeb: any;
  },
): Promise<void> {
  const { tronWallet, apiKey, TronWeb } = deps;

  const tokenSymbol = (options.token || 'USDT').toUpperCase();
  const gasfreeNetwork = options.network || 'nile';
  const networkKey = normalizeNetwork(gasfreeNetwork);
  const baseUrl = (GASFREE_API_BASE_URLS as Record<string, string>)[networkKey];

  if (!baseUrl) {
    console.error(`Error: GasFree not supported on "${gasfreeNetwork}". Supported: mainnet, nile, shasta`);
    process.exit(1);
  }

  const tronWebOpts: any = { fullHost: tronRpcUrl(networkKey), privateKey: TRONWEB_READONLY_DUMMY_KEY };
  if (apiKey) tronWebOpts.headers = { 'TRON-PRO-API-KEY': apiKey };
  const tronWeb = new TronWeb(tronWebOpts);

  // Bind the signer to the requested network so any chain-reading signer
  // capability targets the same chain the activation runs on.
  const tronSigner = await createClientTronSigner(tronWallet as any, { network: networkKey, apiKey });
  const walletAddress = tronSigner.address;
  const gasFreeClient = new GasFreeAPIClient(baseUrl);

  // Step 1: Query account info
  console.error(`[gasfree-activate] Network: ${gasfreeNetwork}, Wallet: ${walletAddress}, Token: ${tokenSymbol}`);
  const accountInfo = await gasFreeClient.getAddressInfo(walletAddress);
  const gasFreeAddr = accountInfo.gasFreeAddress;

  console.error(`[gasfree-activate] GasFree address: ${gasFreeAddr}`);
  console.error(`[gasfree-activate] Active: ${accountInfo.active}, AllowSubmit: ${accountInfo.allowSubmit}, Nonce: ${accountInfo.nonce}`);

  if (accountInfo.active) {
    const result = { status: 'already_active', network: gasfreeNetwork, wallet: walletAddress, gasFreeAddress: gasFreeAddr };
    process.stdout.write(JSON.stringify(result, null, 2) + '\n');
    return;
  }

  if (!accountInfo.allowSubmit) {
    console.error('[gasfree-activate] Error: Account not active and allowSubmit is false.');
    process.exit(1);
  }

  const asset = accountInfo.assets.find((a: any) => a.tokenSymbol === tokenSymbol);
  if (!asset) {
    console.error(`[gasfree-activate] Error: Token ${tokenSymbol} not found. Available: ${accountInfo.assets.map((a: any) => a.tokenSymbol).join(', ')}`);
    process.exit(1);
  }

  const tokenAddress = asset.tokenAddress;
  const decimals = asset.decimal;
  const activateFee = BigInt(asset.activateFee || 0);
  const transferFee = BigInt(asset.transferFee || 0);
  const totalFees = activateFee + transferFee;
  const oneUnit = BigInt(10 ** decimals);
  const transferAmount = totalFees + oneUnit;

  const fmt = (v: bigint) => `${Number(v) / 10 ** decimals} ${tokenSymbol}`;
  console.error(`[gasfree-activate] activateFee=${fmt(activateFee)}, transferFee=${fmt(transferFee)}, total to send=${fmt(transferAmount)}`);

  // Step 2: Check wallet balance
  const contract = await tronWeb.contract().at(tokenAddress);
  const walletBalance = BigInt((await contract.methods.balanceOf(walletAddress).call()).toString());
  console.error(`[gasfree-activate] Wallet balance: ${fmt(walletBalance)}`);

  if (walletBalance < transferAmount) {
    console.error(`[gasfree-activate] Error: Insufficient balance. Need ${fmt(transferAmount)}, have ${fmt(walletBalance)}`);
    process.exit(1);
  }

  // Step 3: Transfer tokens to GasFree address
  console.error(`[gasfree-activate] Transferring ${fmt(transferAmount)} to GasFree address ${gasFreeAddr}...`);
  const gasFreeHexAddress = tronWeb.address.toHex(gasFreeAddr);
  const trigger = await tronWeb.transactionBuilder.triggerSmartContract(
    tokenAddress,
    'transfer(address,uint256)',
    { feeLimit: 100_000_000, callValue: 0 },
    [
      { type: 'address', value: gasFreeHexAddress },
      { type: 'uint256', value: transferAmount.toString() },
    ],
    walletAddress,
  );
  if (!trigger?.result?.result || !trigger.transaction) {
    console.error('[gasfree-activate] Error: Failed to build TRC20 transfer transaction');
    process.exit(1);
  }
  const signedResult = await tronWallet.signTransaction(trigger.transaction as Record<string, unknown>);
  const signedTx = extractSignedTronTx(trigger.transaction as Record<string, unknown>, signedResult);
  const broadcast = await tronWeb.trx.sendRawTransaction(signedTx);
  if (!broadcast?.result) {
    console.error(`[gasfree-activate] Error: Failed to broadcast TRC20 transfer: ${JSON.stringify(broadcast)}`);
    process.exit(1);
  }
  const txId = broadcast.txid || (trigger.transaction as any).txID;
  console.error(`[gasfree-activate] TRC20 transfer tx: ${txId}`);

  console.error(`[gasfree-activate] Waiting for on-chain confirmation...`);
  const confirmed = await waitForTxConfirmation(tronWeb, txId);
  if (!confirmed) {
    console.error('[gasfree-activate] Warning: Tx confirmation timed out, proceeding anyway...');
  }

  // Verify GasFree address balance
  const gfBalance = BigInt((await contract.methods.balanceOf(gasFreeAddr).call()).toString());
  console.error(`[gasfree-activate] GasFree address balance: ${fmt(gfBalance)}`);

  // Step 4: GasFree transfer back to wallet
  const updatedInfo = await gasFreeClient.getAddressInfo(walletAddress);
  const nonce = updatedInfo.nonce;

  const providers = await gasFreeClient.getProviders();
  if (!providers || providers.length === 0) {
    console.error('[gasfree-activate] Error: No GasFree service providers available');
    process.exit(1);
  }
  const provider = providers[0];
  console.error(`[gasfree-activate] Provider: ${provider.address} (${provider.name})`);

  const returnValue = gfBalance - totalFees;
  if (returnValue <= 0n) {
    console.error(`[gasfree-activate] Error: GasFree balance (${fmt(gfBalance)}) not enough to cover fees (${fmt(totalFees)})`);
    process.exit(1);
  }

  const maxFee = totalFees;
  const deadline = gasfreeDeadline(networkKey);

  console.error(`[gasfree-activate] Return: ${fmt(returnValue)}, maxFee: ${fmt(maxFee)}, nonce: ${nonce}`);

  const gasFreeMessage = {
    token: tokenAddress,
    serviceProvider: provider.address,
    user: walletAddress,
    receiver: walletAddress,
    value: returnValue.toString(),
    maxFee: maxFee.toString(),
    deadline: deadline.toString(),
    version: '1',
    nonce: nonce.toString(),
  };
  console.error('[gasfree-activate] Submitting GasFree transaction...');
  const traceId = await signAndSubmitGasFree(tronSigner, gasFreeClient, gasFreeMessage, networkKey);
  console.error(`[gasfree-activate] Trace ID: ${traceId}`);

  // Step 5: Wait for completion
  console.error('[gasfree-activate] Waiting for transaction to complete...');
  const txResult = await gasFreeClient.waitForSuccess(traceId, 180000, 5000);

  // Final verification
  const finalInfo = await gasFreeClient.getAddressInfo(walletAddress);

  const result = {
    status: 'activated',
    network: gasfreeNetwork,
    wallet: walletAddress,
    gasFreeAddress: gasFreeAddr,
    active: finalInfo.active,
    nonce: finalInfo.nonce,
    depositTxId: txId,
    gasFreeTraceId: traceId,
    gasFreeState: txResult.state,
    gasFreeTxHash: txResult.txnHash || null,
  };
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
}

function handleCheck(deps: {
  tronAddress: string | undefined;
  evmAddress: string | undefined;
  apiKey: string | undefined;
}): void {
  const { tronAddress, evmAddress, apiKey } = deps;
  if (tronAddress) {
    console.error(`[OK] TRON Wallet: ${tronAddress}`);
    if (apiKey) console.error(`[OK] TRON_GRID_API_KEY is configured.`);
  }
  if (evmAddress) {
    console.error(`[OK] EVM Wallet: ${evmAddress}`);
  }
  if (!tronAddress && !evmAddress) {
    console.error(`[--] No compatible active wallet resolved from agent-wallet.`);
  }
  console.error(`[OK] GasFree gasless payments enabled (exact_gasfree preferred when available).`);
}

async function main() {
  const debugEnabled = process.env.X402_DEBUG === '1';
  const debug = (...args: any[]) => {
    if (debugEnabled) console.error('[x402:debug]', ...args);
  };

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
      } else { options[key] = 'true'; }
    }
  }

  debug('argv', process.argv.slice(2));
  debug('options', options);

  const url = options.url;
  const entrypoint = options.entrypoint;
  const inputRaw = options.input;
  const methodArg = options.method;

  const apiKey = await findApiKey();
  // Ensure signer/library internals can pick up keys from env
  if (apiKey && !process.env.TRON_GRID_API_KEY) {
    process.env.TRON_GRID_API_KEY = apiKey;
  }

  const [resolvedTronWallet, resolvedEvmWallet] = await Promise.all([
    resolveAgentWallet('tron'),
    resolveAgentWallet('eip155'),
  ]);

  debug('tronWallet', resolvedTronWallet?.address ?? null);
  debug('evmWallet', resolvedEvmWallet?.address ?? null);
  debug('apiKeyConfigured', Boolean(apiKey));

  if (options.check || options.status) {
    handleCheck({
      tronAddress: resolvedTronWallet?.address,
      evmAddress: resolvedEvmWallet?.address,
      apiKey,
    });
    process.exit(0);
  }

  if (options['gasfree-info']) {
    await handleGasFreeInfo(options, resolvedTronWallet?.address);
    process.exit(0);
  }

  if (options['gasfree-activate']) {
    if (!resolvedTronWallet) {
      console.error('Error: A TRON wallet from agent-wallet is required for --gasfree-activate');
      process.exit(1);
    }
    const { TronWeb } = await import('tronweb');
    try {
      await handleGasFreeActivate(options, {
        tronWallet: resolvedTronWallet.wallet,
        apiKey,
        TronWeb,
      });
    } catch (error: any) {
      console.error(`[gasfree-activate] Error: ${error.message || 'Unknown error'}`);
      process.stdout.write(JSON.stringify({ error: error.message || 'Unknown error' }, null, 2) + '\n');
      process.exit(1);
    }
    process.exit(0);
  }

  if (!resolvedTronWallet && !resolvedEvmWallet) {
    console.error('[x402] Warning: no compatible agent-wallet resolved; payment-required endpoints may fail.');
  }

  if (!url) {
    console.error('Error: --url is required');
    process.exit(1);
  }

  debug('entrypoint', entrypoint || null);
  debug('methodArg', methodArg || null);
  debug('inputRaw', inputRaw || null);

  // Redirect console.log to console.error to prevent library pollution of STDOUT
  const originalConsoleLog = console.log;
  console.log = console.error;

  const requestedNetwork = options.network ? normalizeNetwork(options.network) : undefined;
  const registeredNetworks = new Set<string>();
  const client = new x402Client((_version, accepts) => {
    debug('paymentRequirements', accepts.map((r: any) => ({
      scheme: r.scheme, network: r.network, asset: r.asset, amount: r.amount,
    })));
    const candidates = accepts.filter((requirement) =>
      (!requestedNetwork || requirement.network === requestedNetwork) &&
      registeredNetworks.has(requirement.network),
    );
    const selected = candidates.find((requirement) => requirement.scheme === 'exact_gasfree')
      || candidates.find((requirement) => requirement.scheme === 'exact');
    if (!selected) {
      throw new Error(
        `No compatible payment requirement${requestedNetwork ? ` for ${requestedNetwork}` : ''}` +
        `; registered networks: ${[...registeredNetworks].join(', ') || 'none'}`,
      );
    }
    return selected;
  });

  // The core selector pipeline is synchronous, so it cannot pre-check GasFree
  // balances, and the SDK does not retry with another requirement when payload
  // creation throws. Recover here: if exact_gasfree fails (e.g. inactive
  // account or insufficient GasFree wallet balance), rebuild the payload from
  // the remaining advertised requirements (exact) instead of failing the
  // whole request.
  client.onPaymentCreationFailure(async (ctx) => {
    if (ctx.selectedRequirements.scheme !== 'exact_gasfree') return undefined;
    const fallbackAccepts = ctx.paymentRequired.accepts.filter(
      (requirement) => requirement.scheme !== 'exact_gasfree',
    );
    if (fallbackAccepts.length === 0) return undefined;
    const reason = ctx.error instanceof Error ? ctx.error.message : String(ctx.error);
    console.error(`[x402] exact_gasfree payment creation failed (${reason}); falling back to exact.`);
    try {
      const payload = await client.createPaymentPayload({
        ...ctx.paymentRequired,
        accepts: fallbackAccepts,
      });
      return { recovered: true, payload };
    } catch (fallbackError) {
      const fallbackReason = fallbackError instanceof Error ? fallbackError.message : String(fallbackError);
      console.error(`[x402] Fallback to exact also failed (${fallbackReason}); reporting original error.`);
      return undefined;
    }
  });

  if (resolvedTronWallet) {
    const registeredTronNetworks: string[] = [];
    for (const network of TRON_NETWORKS) {
      try {
        const signer = await createClientTronSigner(resolvedTronWallet.wallet as any, { network, apiKey });
        client.register(network, new ExactTronScheme(signer));
        registerExactGasFreeTronScheme(client, { signer, networks: [network] });
        registeredNetworks.add(network);
        registeredTronNetworks.push(network);
      } catch (err: any) {
        console.warn(`[x402] Skipping ${network}: ${err?.message || err}`);
      }
    }
    if (registeredTronNetworks.length > 0) {
      console.error(`[x402] TRON schemes enabled for ${registeredTronNetworks.join(', ')} (exact, exact_gasfree).`);
    } else {
      console.warn('[x402] No TRON payment schemes were registered.');
    }
    debug('registeredTronNetworks', registeredTronNetworks);
  }

  if (resolvedEvmWallet) {
    const registeredEvmNetworks: string[] = [];
    for (const network of EVM_NETWORKS) {
      try {
        const signer = await createClientEvmSigner(resolvedEvmWallet.wallet as any, {
          network,
          rpcUrl: evmRpcUrl(network),
        });
        client.register(network, new ExactEvmScheme(signer));
        registeredNetworks.add(network);
        registeredEvmNetworks.push(network);
      } catch (err: any) {
        console.warn(`[x402] Skipping ${network}: ${err?.message || err}`);
      }
    }
    if (registeredEvmNetworks.length > 0) {
      console.error(`[x402] EVM exact scheme enabled for ${registeredEvmNetworks.join(', ')}.`);
    } else {
      console.warn('[x402] No EVM payment schemes were registered.');
    }
    debug('registeredEvmNetworks', registeredEvmNetworks);
  }

  console.error(`[x402] Payment selector: prefer exact_gasfree, then exact; auto-fallback to exact if gasfree payload creation fails.`);

  let finalUrl = url;
  let finalMethod = methodArg || 'GET';
  let finalBody: string | undefined = undefined;

  if (entrypoint) {
    const baseUrl = url.endsWith('/') ? url.slice(0, -1) : url;
    finalUrl = `${baseUrl}/entrypoints/${entrypoint}/invoke`;
    finalMethod = 'POST';
    let inputData = {};
    if (inputRaw) {
      try { inputData = JSON.parse(inputRaw); } catch (e) { inputData = inputRaw; }
    }
    finalBody = JSON.stringify({ input: inputData });
  } else {
    if (methodArg) finalMethod = methodArg.toUpperCase();
    if (inputRaw) finalBody = inputRaw;
  }

  debug('finalRequest', { method: finalMethod, url: finalUrl, bodyBytes: finalBody ? Buffer.byteLength(finalBody, 'utf8') : 0 });

  try {
    const fetchWithPayment = wrapFetchWithPayment(fetch, client);
    const requestInit: any = {
      method: finalMethod,
      headers: { 'Content-Type': 'application/json' },
      body: finalBody
    };

    console.error(`[x402] Requesting: ${finalMethod} ${finalUrl}`);
    const response = await fetchWithPayment(finalUrl, requestInit);

    const contentType = response.headers.get('content-type') || '';
    let responseBody;

    if (contentType.includes('application/json')) {
      responseBody = await response.json();
    } else if (contentType.includes('image/') || contentType.includes('application/octet-stream')) {
      const buffer = Buffer.from(await response.arrayBuffer());
      const tmpDir = os.tmpdir();
      const isImage = contentType.includes('image/');
      const ext = isImage ? contentType.split('/')[1]?.split(';')[0] || 'bin' : 'bin';
      const fileName = `x402_${isImage ? 'image' : 'binary'}_${Date.now()}_${Math.random().toString(36).substring(7)}.${ext}`;
      const filePath = path.join(tmpDir, fileName);

      fs.writeFileSync(filePath, buffer);
      console.error(`[x402] Binary data saved to: ${filePath}`);
      responseBody = { file_path: filePath, content_type: contentType, bytes: buffer.length };
    } else {
      responseBody = await response.text();
    }

    const paymentResponseHeader = response.headers.get('payment-response');
    if (paymentResponseHeader) {
      try {
        const decoded = Buffer.from(paymentResponseHeader, 'base64').toString('utf8');
        const paymentResult = JSON.parse(decoded) as {
          success?: boolean;
          network?: string;
          transaction?: string;
          errorReason?: string | null;
        };
        const details = [
          `success=${String(paymentResult.success)}`,
          `network=${paymentResult.network || 'unknown'}`,
          `tx=${paymentResult.transaction || 'n/a'}`,
        ];
        if (paymentResult.errorReason) details.push(`errorReason=${paymentResult.errorReason}`);
        console.error(`[x402] Payment result: ${details.join(' ')}`);
      } catch {
        console.error('[x402] Payment result: unable to decode payment-response header');
      }
    } else {
      console.error('[x402] Payment result: no payment-response header');
    }

    process.stdout.write(JSON.stringify({
      status: response.status,
      headers: Object.fromEntries(response.headers.entries()),
      body: responseBody
    }, null, 2) + '\n');
  } catch (error: any) {
    const message = error.message || 'Unknown error';
    const cause = error?.cause as any;
    const debugEnabled = process.env.X402_DEBUG === '1';
    const output: Record<string, unknown> = {
      error: message,
      request: {
        method: finalMethod,
        url: finalUrl,
      },
    };
    if (cause?.shortMessage) output.cause = cause.shortMessage;
    if (cause?.url) output.rpc_url = cause.url;
    if (debugEnabled) output.stack = error.stack || '';

    console.error(`[x402] Error: ${message}`);
    if (typeof output.cause === 'string') {
      console.error(`[x402] Cause: ${output.cause}`);
    }
    if (typeof output.rpc_url === 'string') {
      console.error(`[x402] RPC URL: ${output.rpc_url}`);
    }
    process.stdout.write(JSON.stringify(output, null, 2) + '\n');
    process.exit(1);
  }
}

main();
