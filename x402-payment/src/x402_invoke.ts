#!/usr/bin/env node
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

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
    ExactGasFreeClientMechanism,
    GasFreeAPIClient,
    GASFREE_API_BASE_URLS,
    SufficientBalancePolicy
  } = await import('@bankofai/x402');

  const tronKey = await findPrivateKey('tron');
  const evmKey = await findPrivateKey('evm');
  const apiKey = await findApiKey();

  if (options.check === 'true' || options.status === 'true') {
    if (tronKey) {
      const signer = new TronClientSigner(tronKey);
      console.error(`[OK] TRON Wallet: ${signer.getAddress()}`);
      if (apiKey) console.error(`[OK] TRON_GRID_API_KEY is configured.`);
    }
    if (evmKey) {
      const signer = new EvmClientSigner(evmKey);
      console.error(`[OK] EVM Wallet: ${signer.getAddress()}`);
    }
    if (process.env.GASFREE_API_KEY && process.env.GASFREE_API_SECRET) {
      console.error(`[OK] GasFree API credentials configured (will prefer exact_gasfree).`);
    } else {
      console.error(`[--] GasFree API credentials not configured (GASFREE_API_KEY / GASFREE_API_SECRET).`);
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

  if (tronKey) {
    const tronWebOptions: any = { fullHost: 'https://nile.trongrid.io', privateKey: tronKey };
    if (networkName === 'mainnet') tronWebOptions.fullHost = 'https://api.trongrid.io';
    if (networkName === 'shasta') tronWebOptions.fullHost = 'https://api.shasta.trongrid.io';
    if (apiKey) tronWebOptions.headers = { 'TRON-PRO-API-KEY': apiKey };

    const tw = new TronWeb(tronWebOptions);
    const signer = new TronClientSigner(tronKey);

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
    const signer = new EvmClientSigner(evmKey);
    client.register('eip155:*', new ExactEvmClientMechanism(signer));
    client.register('eip155:*', new ExactPermitEvmClientMechanism(signer));
    console.error(`[x402] EVM mechanisms enabled.`);
  }

  client.registerPolicy(new SufficientBalancePolicy(client));

  // Prefer exact_gasfree when GasFree API credentials are configured
  const gasFreeApiKey = process.env.GASFREE_API_KEY;
  const gasFreeApiSecret = process.env.GASFREE_API_SECRET;
  if (gasFreeApiKey && gasFreeApiSecret) {
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
