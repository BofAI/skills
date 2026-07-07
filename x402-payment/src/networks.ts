// Shared network configuration and GasFree helpers for the x402-payment skill.
// Both entry points (x402_invoke.ts, gasfree_withdraw_all.ts) import from here so
// the supported-network list, RPC selection, and GasFree signing flow have a
// single source of truth.
import { assembleGasFreeTransaction } from '@bankofai/x402-tron/gasfree';

// Read-only TronWeb instantiation only; never use this key for signing.
// If this key is ever used to sign, it will produce valid signatures for a known public address.
export const TRONWEB_READONLY_DUMMY_KEY = '0000000000000000000000000000000000000000000000000000000000000001';

// The networks this skill registers payment schemes for.
export const TRON_NETWORKS = ['tron:nile', 'tron:mainnet', 'tron:shasta'] as const;
export const EVM_NETWORKS = ['eip155:97', 'eip155:56'] as const;

// Short-name aliases accepted by --network, mapped to CAIP-2 ids.
const NETWORK_IDS: Record<string, string> = {
  mainnet: 'tron:mainnet',
  nile: 'tron:nile',
  shasta: 'tron:shasta',
  bsc: 'eip155:56',
  'bsc-mainnet': 'eip155:56',
  'bsc-testnet': 'eip155:97',
};

export function normalizeNetwork(network: string): string {
  return NETWORK_IDS[network] || network;
}

// Resolved lazily so a TRON_GRID_API_KEY injected from x402-config.json after
// startup still selects the authenticated mainnet endpoint.
export function tronRpcUrl(networkId: string): string | undefined {
  switch (networkId) {
    case 'tron:mainnet':
      return process.env.TRON_GRID_API_KEY ? 'https://api.trongrid.io' : 'https://hptg.bankofai.io';
    case 'tron:nile':
      return 'https://nile.trongrid.io';
    case 'tron:shasta':
      return 'https://api.shasta.trongrid.io';
    default:
      return undefined;
  }
}

// Resolve a per-chain EVM RPC URL. Each chain reads its own env var so a custom
// RPC for one never bleeds into another.
export function evmRpcUrl(network: string): string | undefined {
  const chainId = network.split(':')[1];
  return process.env[`EVM_RPC_URL_${chainId}`];
}

// The GasFree relayer caps how far ahead a deadline may be (~600s on mainnet,
// ~3600s on testnets); stay inside the window like the SDK's own gasfree path.
export function gasfreeDeadline(networkId: string): number {
  return Math.floor(Date.now() / 1000) + (networkId === 'tron:mainnet' ? 590 : 3590);
}

export interface GasFreeMessage {
  token: string;
  serviceProvider: string;
  user: string;
  receiver: string;
  value: string;
  maxFee: string;
  deadline: string;
  version: string;
  nonce: string;
}

// Assemble the EIP-712 payload, sign it, and submit it to the GasFree relayer.
// The relayer expects the original string-valued message; only the signature is
// computed over the assembled (bigint-typed) form.
export async function signAndSubmitGasFree(
  signer: { signTypedData(args: any): Promise<string> },
  gasFreeClient: { submit(message: any, signature: string): Promise<string> },
  message: GasFreeMessage,
  networkId: string,
): Promise<string> {
  const assembled = assembleGasFreeTransaction(message, networkId as any);
  const signature = await signer.signTypedData({
    domain: assembled.domain,
    types: assembled.types,
    primaryType: assembled.primaryType,
    message: assembled.message,
  });
  return gasFreeClient.submit(message, signature);
}
