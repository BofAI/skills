#!/usr/bin/env node
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

interface AgentWalletConfig {
  tronWalletName?: string;
  evmWalletName?: string;
  secretsDir: string;
  password: string;
}

function expandHomePath(inputPath: string): string {
  if (inputPath === '~') return os.homedir();
  if (inputPath.startsWith('~/')) return path.join(os.homedir(), inputPath.slice(2));
  return inputPath;
}

function findAgentWalletConfig(): AgentWalletConfig | undefined {
  const tronName = process.env.TRON_AGENT_WALLET_NAME;
  const evmName = process.env.EVM_AGENT_WALLET_NAME || process.env.BSC_AGENT_WALLET_NAME;
  const secretsDir = expandHomePath(process.env.AGENT_WALLET_SECRETS_DIR || '~/.agent-wallet');
  const password = process.env.AGENT_WALLET_PASSWORD || '';

  if (!tronName && !evmName) {
    // Check config files
    const configFiles = [
      path.join(process.cwd(), 'x402-config.json'),
      path.join(os.homedir(), '.x402-config.json')
    ];
    for (const file of configFiles) {
      if (fs.existsSync(file)) {
        try {
          const config = JSON.parse(fs.readFileSync(file, 'utf8'));
          if (config.agent_wallet) {
            return {
              tronWalletName: config.agent_wallet.tron_wallet_name,
              evmWalletName: config.agent_wallet.evm_wallet_name || config.agent_wallet.bsc_wallet_name,
              secretsDir: expandHomePath(config.agent_wallet.secrets_dir || secretsDir),
              password: config.agent_wallet.password || password,
            };
          }
        } catch (e) { /* ignore */ }
      }
    }
    return undefined;
  }

  return { tronWalletName: tronName, evmWalletName: evmName, secretsDir, password };
}

async function findPrivateKey(type: 'tron' | 'evm'): Promise<string | undefined> {
  // 1. Check environment variables
  if (type === 'tron') {
    if (process.env.TRON_PRIVATE_KEY) return process.env.TRON_PRIVATE_KEY;
  } else {
    if (process.env.EVM_PRIVATE_KEY) return process.env.EVM_PRIVATE_KEY;
    if (process.env.ETH_PRIVATE_KEY) return process.env.ETH_PRIVATE_KEY;
  }
  if (process.env.PRIVATE_KEY) return process.env.PRIVATE_KEY;

  // 2. Check local config files
  const configFiles = [
    path.join(process.cwd(), 'x402-config.json'),
    path.join(os.homedir(), '.x402-config.json')
  ];

  for (const file of configFiles) {
    if (fs.existsSync(file)) {
      try {
        const config = JSON.parse(fs.readFileSync(file, 'utf8'));
        if (type === 'tron') {
          const key = config.tron_private_key || config.private_key;
          if (key) return key;
        } else {
          const key = config.evm_private_key || config.eth_private_key || config.private_key;
          if (key) return key;
        }
      } catch (e) { /* ignore */ }
    }
  }

  // 3. Check mcporter config
  const mcporterPath = path.join(os.homedir(), '.mcporter', 'mcporter.json');
  if (fs.existsSync(mcporterPath)) {
    try {
      const config = JSON.parse(fs.readFileSync(mcporterPath, 'utf8'));
      if (config.mcpServers) {
        for (const serverName in config.mcpServers) {
          const s = config.mcpServers[serverName];
          if (type === 'tron' && s?.env?.TRON_PRIVATE_KEY) return s.env.TRON_PRIVATE_KEY;
          if (type === 'evm' && (s?.env?.EVM_PRIVATE_KEY || s?.env?.ETH_PRIVATE_KEY)) {
            return s.env.EVM_PRIVATE_KEY || s.env.ETH_PRIVATE_KEY;
          }
          if (s?.env?.PRIVATE_KEY) return s.env.PRIVATE_KEY;
        }
      }
    } catch (e) { /* ignore */ }
  }

  return undefined;
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

  const mcporterPath = path.join(os.homedir(), '.mcporter', 'mcporter.json');
  if (fs.existsSync(mcporterPath)) {
    try {
      const config = JSON.parse(fs.readFileSync(mcporterPath, 'utf8'));
      if (config.mcpServers) {
        for (const serverName in config.mcpServers) {
          const s = config.mcpServers[serverName];
          if (s?.env?.TRON_GRID_API_KEY) return s.env.TRON_GRID_API_KEY;
        }
      }
    } catch (e) { /* ignore */ }
  }
  return undefined;
}

async function hasPrivateKeyConfig(): Promise<boolean> {
  return Boolean((await findPrivateKey('tron')) || (await findPrivateKey('evm')));
}

function hasAgentWalletConfig(config?: AgentWalletConfig): boolean {
  return Boolean(config && Boolean(config.password));
}

async function findGasFreeCredentials(): Promise<{ apiKey: string; apiSecret: string } | undefined> {
  if (process.env.GASFREE_API_KEY && process.env.GASFREE_API_SECRET) {
    return { apiKey: process.env.GASFREE_API_KEY, apiSecret: process.env.GASFREE_API_SECRET };
  }

  const configFiles = [
    path.join(process.cwd(), 'x402-config.json'),
    path.join(os.homedir(), '.x402-config.json')
  ];

  for (const file of configFiles) {
    if (fs.existsSync(file)) {
      try {
        const config = JSON.parse(fs.readFileSync(file, 'utf8'));
        const key = (config.gasfree_api_key || '').trim();
        const secret = (config.gasfree_api_secret || '').trim();
        if (key && secret) return { apiKey: key, apiSecret: secret };
      } catch (e) { /* ignore */ }
    }
  }

  const mcporterPath = path.join(os.homedir(), '.mcporter', 'mcporter.json');
  if (fs.existsSync(mcporterPath)) {
    try {
      const config = JSON.parse(fs.readFileSync(mcporterPath, 'utf8'));
      if (config.mcpServers) {
        for (const serverName in config.mcpServers) {
          const s = config.mcpServers[serverName];
          const key = (s?.env?.GASFREE_API_KEY || '').trim();
          const secret = (s?.env?.GASFREE_API_SECRET || '').trim();
          if (key && secret) return { apiKey: key, apiSecret: secret };
        }
      }
    } catch (e) { /* ignore */ }
  }
  return undefined;
}

const TRON_RPC_URLS: Record<string, string> = {
  mainnet: 'https://api.trongrid.io',
  nile: 'https://nile.trongrid.io',
  shasta: 'https://api.shasta.trongrid.io',
};

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
  deps: {
    tronKey: string | undefined;
    gasFreeCredentials: { apiKey: string; apiSecret: string } | undefined;
    TronClientSigner: any;
    GasFreeAPIClient: any;
    GASFREE_API_BASE_URLS: Record<string, string>;
  },
): Promise<void> {
  const { tronKey, gasFreeCredentials, TronClientSigner, GasFreeAPIClient, GASFREE_API_BASE_URLS } = deps;

  if (!gasFreeCredentials) {
    console.error('Error: GasFree API credentials (GASFREE_API_KEY / GASFREE_API_SECRET) are required for --gasfree-info');
    process.exit(1);
  }

  let walletAddress: string;
  if (options['wallet']) {
    walletAddress = options['wallet'];
  } else if (tronKey) {
    const signer = new TronClientSigner(tronKey);
    walletAddress = signer.getAddress();
  } else {
    console.error('Error: Provide --wallet <address> or set TRON_PRIVATE_KEY');
    process.exit(1);
  }

  const gasfreeNetwork = options.network || 'mainnet';
  const networkKey = `tron:${gasfreeNetwork}`;
  const baseUrl = GASFREE_API_BASE_URLS[networkKey];

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
    tronKey: string;
    apiKey: string | undefined;
    gasFreeCredentials: { apiKey: string; apiSecret: string };
    TronWeb: any;
    TronClientSigner: any;
    GasFreeAPIClient: any;
    GASFREE_API_BASE_URLS: Record<string, string>;
    getChainId: any;
  },
): Promise<void> {
  const { tronKey, apiKey, TronWeb, TronClientSigner, GasFreeAPIClient, GASFREE_API_BASE_URLS, getChainId } = deps;

  const tokenSymbol = (options.token || 'USDT').toUpperCase();
  const gasfreeNetwork = options.network || 'nile';
  const networkKey = `tron:${gasfreeNetwork}`;
  const baseUrl = GASFREE_API_BASE_URLS[networkKey];

  if (!baseUrl) {
    console.error(`Error: GasFree not supported on "${gasfreeNetwork}". Supported: mainnet, nile, shasta`);
    process.exit(1);
  }

  const tronWebOpts: any = { fullHost: TRON_RPC_URLS[gasfreeNetwork], privateKey: tronKey };
  if (apiKey) tronWebOpts.headers = { 'TRON-PRO-API-KEY': apiKey };
  const tronWeb = new TronWeb(tronWebOpts);

  const signer = new TronClientSigner(tronKey);
  const walletAddress = signer.getAddress();
  const gasFreeClient = new GasFreeAPIClient(baseUrl);

  // @ts-ignore - CJS module with named exports
  const { TronGasFree } = await import('@gasfree/gasfree-sdk');

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
  const txn = await contract.methods.transfer(gasFreeAddr, transferAmount.toString()).send();
  const txId = typeof txn === 'string' ? txn : txn.txid || txn;
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
  const deadline = Math.floor(Date.now() / 1000) + 3600;

  console.error(`[gasfree-activate] Return: ${fmt(returnValue)}, maxFee: ${fmt(maxFee)}, nonce: ${nonce}`);

  const chainId = parseInt(getChainId(networkKey), 10);
  const gasFree = new TronGasFree({ chainId });

  const { domain, types, message } = gasFree.assembleGasFreeTransactionJson({
    token: tokenAddress,
    serviceProvider: provider.address,
    user: walletAddress,
    receiver: walletAddress,
    value: returnValue.toString(),
    maxFee: maxFee.toString(),
    deadline: deadline.toString(),
    version: '1',
    nonce: nonce.toString(),
  });

  const signature = await signer.signTypedData(domain, types, message, 'GasFreeTransaction');

  console.error('[gasfree-activate] Submitting GasFree transaction...');
  const traceId = await gasFreeClient.submit(domain, message, signature);
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
  tronKey: string | undefined;
  evmKey: string | undefined;
  apiKey: string | undefined;
  gasFreeCredentials: { apiKey: string; apiSecret: string } | undefined;
  TronClientSigner: any;
  EvmClientSigner: any;
}): void {
  const { tronKey, evmKey, apiKey, gasFreeCredentials, TronClientSigner, EvmClientSigner } = deps;
  if (tronKey) {
    const signer = new TronClientSigner(tronKey);
    console.error(`[OK] TRON Wallet: ${signer.getAddress()}`);
    if (apiKey) console.error(`[OK] TRON_GRID_API_KEY is configured.`);
  }
  if (evmKey) {
    const signer = new EvmClientSigner(evmKey);
    console.error(`[OK] EVM Wallet: ${signer.getAddress()}`);
  }
  if (gasFreeCredentials) {
    console.error(`[OK] GasFree API credentials configured (will prefer exact_gasfree).`);
  } else {
    console.error(`[--] GasFree API credentials not configured (GASFREE_API_KEY / GASFREE_API_SECRET).`);
  }
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
      } else { options[key] = 'true'; }
    }
  }

  const url = options.url;
  const entrypoint = options.entrypoint;
  const inputRaw = options.input;
  const methodArg = options.method;
  const networkName = options.network || 'nile';

  // Use dynamic imports
  // @ts-ignore
  const { TronWeb } = await import('tronweb');
  (global as any).TronWeb = TronWeb;

  const {
    TronClientSigner,
    EvmClientSigner,
    X402Client,
    X402FetchClient,
    ExactTronClientMechanism,
    ExactEvmClientMechanism,
    ExactPermitTronClientMechanism,
    ExactPermitEvmClientMechanism,
    AgentWalletAdapter,
    ExactGasFreeClientMechanism,
    GasFreeAPIClient,
    GASFREE_API_BASE_URLS,
    SufficientBalancePolicy,
    getChainId,
  } = await import('@bankofai/x402');

  const apiKey = await findApiKey();
  const gasFreeCredentials = await findGasFreeCredentials();
  const agentWalletConfig = findAgentWalletConfig();
  const hasAgentWallet = hasAgentWalletConfig(agentWalletConfig);
  const hasPrivateKey = await hasPrivateKeyConfig();
  const useAgentWallet = hasAgentWallet;

  // Ensure signer/library internals can pick up keys from env
  if (apiKey && !process.env.TRON_GRID_API_KEY) {
    process.env.TRON_GRID_API_KEY = apiKey;
  }
  if (gasFreeCredentials) {
    if (!process.env.GASFREE_API_KEY) process.env.GASFREE_API_KEY = gasFreeCredentials.apiKey;
    if (!process.env.GASFREE_API_SECRET) process.env.GASFREE_API_SECRET = gasFreeCredentials.apiSecret;
  }

  if (options.check === 'true' || options.status === 'true') {
    console.error(`[x402] Wallet mode: ${useAgentWallet ? 'agent_wallet' : 'private_key'} (auto-detected)`);
    console.error(`[x402] Agent wallet available: ${hasAgentWallet ? 'yes' : 'no'}`);
    console.error(`[x402] Private key available: ${hasPrivateKey ? 'yes' : 'no'}`);
    if (useAgentWallet) {
      if (agentWalletConfig) {
        if (agentWalletConfig.tronWalletName) console.error(`[OK] TRON Agent Wallet: ${agentWalletConfig.tronWalletName}`);
        if (agentWalletConfig.evmWalletName) console.error(`[OK] EVM Agent Wallet: ${agentWalletConfig.evmWalletName}`);
        console.error(`[OK] Secrets dir: ${agentWalletConfig.secretsDir}`);
      } else {
        console.error(`[WARN] No agent wallet configuration found.`);
      }
    } else {
      const tronKey = await findPrivateKey('tron');
      const evmKey = await findPrivateKey('evm');
      if (tronKey) {
        const signer = TronClientSigner.fromPrivateKey(tronKey);
        console.error(`[OK] TRON Wallet: ${signer.getAddress()}`);
        if (apiKey) console.error(`[OK] TRON_GRID_API_KEY is configured.`);
      }
      if (evmKey) {
        const signer = EvmClientSigner.fromPrivateKey(evmKey);
        console.error(`[OK] EVM Wallet: ${signer.getAddress()}`);
      }
    }
    if (gasFreeCredentials) {
      console.error(`[OK] GasFree API credentials configured (will prefer exact_gasfree).`);
    } else {
      console.error(`[--] GasFree API credentials not configured (GASFREE_API_KEY / GASFREE_API_SECRET).`);
    }
    process.exit(0);
  }

  const tronKey = await findPrivateKey('tron');
  const evmKey = await findPrivateKey('evm');

  if (options['gasfree-info']) {
    await handleGasFreeInfo(options, {
      tronKey, gasFreeCredentials, TronClientSigner, GasFreeAPIClient,
      GASFREE_API_BASE_URLS: GASFREE_API_BASE_URLS as Record<string, string>,
    });
    process.exit(0);
  }

  if (options['gasfree-activate']) {
    if (!tronKey) {
      console.error('Error: TRON_PRIVATE_KEY is required for --gasfree-activate');
      process.exit(1);
    }
    if (!gasFreeCredentials) {
      console.error('Error: GasFree API credentials (GASFREE_API_KEY / GASFREE_API_SECRET) are required for --gasfree-activate');
      process.exit(1);
    }
    try {
      await handleGasFreeActivate(options, {
        tronKey, apiKey, gasFreeCredentials, TronWeb, TronClientSigner, GasFreeAPIClient,
        GASFREE_API_BASE_URLS: GASFREE_API_BASE_URLS as Record<string, string>,
        getChainId,
      });
    } catch (error: any) {
      console.error(`[gasfree-activate] Error: ${error.message || 'Unknown error'}`);
      process.stdout.write(JSON.stringify({ error: error.message || 'Unknown error' }, null, 2) + '\n');
      process.exit(1);
    }
    process.exit(0);
  }

  if (!url) {
    console.error('Error: --url is required');
    process.exit(1);
  }

  // Redirect console.log to console.error to prevent library pollution of STDOUT
  const originalConsoleLog = console.log;
  console.log = console.error;

  const client = new X402Client();
  console.error(`[x402] Using wallet mode: ${useAgentWallet ? 'agent_wallet' : 'private_key'} (auto-detected)`);

  if (useAgentWallet) {
    // --- Agent Wallet Mode ---
    const awConfigCandidate = agentWalletConfig;
    if (!awConfigCandidate || (!awConfigCandidate.tronWalletName && !awConfigCandidate.evmWalletName)) {
      console.error('Error: Agent wallet configuration not found. Set TRON_AGENT_WALLET_NAME / EVM_AGENT_WALLET_NAME together with AGENT_WALLET_PASSWORD, or configure agent_wallet in x402-config.json.');
      process.exit(1);
    }
    const awPassword = awConfigCandidate!.password;
    if (!awPassword) {
      console.error('Error: AGENT_WALLET_PASSWORD is required for agent wallet mode.');
      process.exit(1);
    }
    const awConfig = awConfigCandidate!;

    let WalletFactory: any;
    try {
      ({ WalletFactory } = await import('@bankofai/agent-wallet'));
    } catch {
      console.error('Error: Agent wallet mode requires `@bankofai/agent-wallet` package.');
      process.exit(1);
    }

    const provider = WalletFactory({
      secretsDir: awConfig.secretsDir,
      password: awPassword,
    });

    if (awConfig.tronWalletName) {
      const agentWallet = await provider.getWallet(awConfig.tronWalletName);
      const wallet = await AgentWalletAdapter.create(agentWallet);
      const signer = TronClientSigner.fromWallet(wallet);

      // Build GasFree API clients per network
      const gasFreeClients: Record<string, any> = {};
      for (const [networkId, baseUrl] of Object.entries(GASFREE_API_BASE_URLS as Record<string, string>)) {
        gasFreeClients[networkId] = new GasFreeAPIClient(baseUrl);
      }

      const networks = ['mainnet', 'nile', 'shasta', '*'];
      for (const net of networks) {
        const networkId = net === '*' ? 'tron:*' : `tron:${net}`;
        client.register(networkId, new ExactTronClientMechanism(signer));
        client.register(networkId, new ExactPermitTronClientMechanism(signer));
        client.register(networkId, new ExactGasFreeClientMechanism(signer, gasFreeClients));
      }
      console.error(`[x402] TRON mechanisms enabled (agent wallet: ${awConfig.tronWalletName}).`);
    }

    if (awConfig.evmWalletName) {
      const agentWallet = await provider.getWallet(awConfig.evmWalletName);
      const wallet = await AgentWalletAdapter.create(agentWallet);
      const signer = EvmClientSigner.fromWallet(wallet);
      client.register('eip155:*', new ExactEvmClientMechanism(signer));
      client.register('eip155:*', new ExactPermitEvmClientMechanism(signer));
      console.error(`[x402] EVM mechanisms enabled (agent wallet: ${awConfig.evmWalletName}).`);
    }
  } else {
    // --- Private Key Mode ---
    if (tronKey) {
      const tronWebOptions: any = { fullHost: TRON_RPC_URLS[networkName] || TRON_RPC_URLS.nile, privateKey: tronKey };
      if (apiKey) tronWebOptions.headers = { 'TRON-PRO-API-KEY': apiKey };

      const signer = TronClientSigner.fromPrivateKey(tronKey);

      // Build GasFree API clients per network
      const gasFreeClients: Record<string, any> = {};
      for (const [networkId, baseUrl] of Object.entries(GASFREE_API_BASE_URLS as Record<string, string>)) {
        gasFreeClients[networkId] = new GasFreeAPIClient(baseUrl);
      }

      const networks = ['mainnet', 'nile', 'shasta', '*'];
      for (const net of networks) {
        const networkId = net === '*' ? 'tron:*' : `tron:${net}`;
        client.register(networkId, new ExactTronClientMechanism(signer));
        client.register(networkId, new ExactPermitTronClientMechanism(signer));
        client.register(networkId, new ExactGasFreeClientMechanism(signer, gasFreeClients));
      }
      console.error(`[x402] TRON mechanisms enabled (exact, exact_permit, exact_gasfree).`);
    }

    if (evmKey) {
      const signer = EvmClientSigner.fromPrivateKey(evmKey);
      client.register('eip155:*', new ExactEvmClientMechanism(signer));
      client.register('eip155:*', new ExactPermitEvmClientMechanism(signer));
      console.error(`[x402] EVM mechanisms enabled.`);
    }
  }

  client.registerPolicy(new SufficientBalancePolicy(client));

  // Prefer exact_gasfree when GasFree API credentials are configured
  if (gasFreeCredentials) {
    client.registerPolicy({
      apply(requirements: any[]) {
        const gasfree = requirements.filter((r: any) => r.scheme === 'exact_gasfree');
        const others = requirements.filter((r: any) => r.scheme !== 'exact_gasfree');
        return [...gasfree, ...others];
      }
    });
    console.error(`[x402] GasFree priority policy enabled.`);
  }

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

  try {
    const fetchClient = new X402FetchClient(client);
    const requestInit: any = {
      method: finalMethod,
      headers: { 'Content-Type': 'application/json' },
      body: finalBody
    };

    console.error(`[x402] Requesting: ${finalMethod} ${finalUrl}`);
    const response = await fetchClient.request(finalUrl, requestInit);

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

    process.stdout.write(JSON.stringify({
      status: response.status,
      headers: Object.fromEntries(response.headers.entries()),
      body: responseBody
    }, null, 2) + '\n');
  } catch (error: any) {
    let message = error.message || 'Unknown error';
    let stack = error.stack || '';

    // Sanitize any potential private key leaks in error messages/stacks
    const tronKey = await findPrivateKey('tron');
    const evmKey = await findPrivateKey('evm');
    const keys = [tronKey, evmKey].filter(Boolean) as string[];
    for (const key of keys) {
      const escapedKey = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const keyRegex = new RegExp(escapedKey, 'g');
      message = message.replace(keyRegex, '[REDACTED]');
      stack = stack.replace(keyRegex, '[REDACTED]');
    }

    console.error(`[x402] Error: ${message}`);
    process.stdout.write(JSON.stringify({
      error: message,
      stack: stack
    }, null, 2) + '\n');
    process.exit(1);
  }
}

main();
