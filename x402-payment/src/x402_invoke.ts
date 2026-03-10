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
    SufficientBalancePolicy
  } = await import('@bankofai/x402');

  const apiKey = await findApiKey();
  const agentWalletConfig = findAgentWalletConfig();
  const hasAgentWallet = hasAgentWalletConfig(agentWalletConfig);
  const hasPrivateKey = await hasPrivateKeyConfig();
  const useAgentWallet = hasAgentWallet;

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
      const networks = ['mainnet', 'nile', 'shasta', '*'];
      for (const net of networks) {
        const networkId = net === '*' ? 'tron:*' : `tron:${net}`;
        client.register(networkId, new ExactTronClientMechanism(signer));
        client.register(networkId, new ExactPermitTronClientMechanism(signer));
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
    const tronKey = await findPrivateKey('tron');
    const evmKey = await findPrivateKey('evm');

    if (tronKey) {
      const tronWebOptions: any = { fullHost: 'https://nile.trongrid.io', privateKey: tronKey };
      if (networkName === 'mainnet') tronWebOptions.fullHost = 'https://api.trongrid.io';
      if (networkName === 'shasta') tronWebOptions.fullHost = 'https://api.shasta.trongrid.io';
      if (apiKey) tronWebOptions.headers = { 'TRON-PRO-API-KEY': apiKey };

      const tw = new TronWeb(tronWebOptions);
      const signer = TronClientSigner.fromPrivateKey(tronKey);
      const networks = ['mainnet', 'nile', 'shasta', '*'];
      for (const net of networks) {
        const networkId = net === '*' ? 'tron:*' : `tron:${net}`;
        client.register(networkId, new ExactTronClientMechanism(signer));
        client.register(networkId, new ExactPermitTronClientMechanism(signer));
      }
      console.error(`[x402] TRON mechanisms enabled.`);
    }

    if (evmKey) {
      const signer = EvmClientSigner.fromPrivateKey(evmKey);
      client.register('eip155:*', new ExactEvmClientMechanism(signer));
      client.register('eip155:*', new ExactPermitEvmClientMechanism(signer));
      console.error(`[x402] EVM mechanisms enabled.`);
    }
  }

  client.registerPolicy(new SufficientBalancePolicy(client));


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
