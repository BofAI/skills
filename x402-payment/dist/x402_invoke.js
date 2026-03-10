#!/usr/bin/env node
import { createRequire as __WEBPACK_EXTERNAL_createRequire } from "module";
/******/ var __webpack_modules__ = ({

/***/ 2613:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("assert");

/***/ }),

/***/ 6982:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("crypto");

/***/ }),

/***/ 4434:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("events");

/***/ }),

/***/ 9896:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("fs");

/***/ }),

/***/ 8611:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("http");

/***/ }),

/***/ 5675:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("http2");

/***/ }),

/***/ 5692:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("https");

/***/ }),

/***/ 7598:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:crypto");

/***/ }),

/***/ 3024:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:fs");

/***/ }),

/***/ 8161:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:os");

/***/ }),

/***/ 6760:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:path");

/***/ }),

/***/ 6928:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("path");

/***/ }),

/***/ 2203:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("stream");

/***/ }),

/***/ 7016:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("url");

/***/ }),

/***/ 9023:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("util");

/***/ }),

/***/ 3106:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("zlib");

/***/ })

/******/ });
/************************************************************************/
/******/ // The module cache
/******/ var __webpack_module_cache__ = {};
/******/ 
/******/ // The require function
/******/ function __nccwpck_require__(moduleId) {
/******/ 	// Check if module is in cache
/******/ 	var cachedModule = __webpack_module_cache__[moduleId];
/******/ 	if (cachedModule !== undefined) {
/******/ 		return cachedModule.exports;
/******/ 	}
/******/ 	// Create a new module (and put it into the cache)
/******/ 	var module = __webpack_module_cache__[moduleId] = {
/******/ 		// no module.id needed
/******/ 		// no module.loaded needed
/******/ 		exports: {}
/******/ 	};
/******/ 
/******/ 	// Execute the module function
/******/ 	var threw = true;
/******/ 	try {
/******/ 		__webpack_modules__[moduleId].call(module.exports, module, module.exports, __nccwpck_require__);
/******/ 		threw = false;
/******/ 	} finally {
/******/ 		if(threw) delete __webpack_module_cache__[moduleId];
/******/ 	}
/******/ 
/******/ 	// Return the exports of the module
/******/ 	return module.exports;
/******/ }
/******/ 
/******/ // expose the modules object (__webpack_modules__)
/******/ __nccwpck_require__.m = __webpack_modules__;
/******/ 
/************************************************************************/
/******/ /* webpack/runtime/create fake namespace object */
/******/ (() => {
/******/ 	var getProto = Object.getPrototypeOf ? (obj) => (Object.getPrototypeOf(obj)) : (obj) => (obj.__proto__);
/******/ 	var leafPrototypes;
/******/ 	// create a fake namespace object
/******/ 	// mode & 1: value is a module id, require it
/******/ 	// mode & 2: merge all properties of value into the ns
/******/ 	// mode & 4: return value when already ns object
/******/ 	// mode & 16: return value when it's Promise-like
/******/ 	// mode & 8|1: behave like require
/******/ 	__nccwpck_require__.t = function(value, mode) {
/******/ 		if(mode & 1) value = this(value);
/******/ 		if(mode & 8) return value;
/******/ 		if(typeof value === 'object' && value) {
/******/ 			if((mode & 4) && value.__esModule) return value;
/******/ 			if((mode & 16) && typeof value.then === 'function') return value;
/******/ 		}
/******/ 		var ns = Object.create(null);
/******/ 		__nccwpck_require__.r(ns);
/******/ 		var def = {};
/******/ 		leafPrototypes = leafPrototypes || [null, getProto({}), getProto([]), getProto(getProto)];
/******/ 		for(var current = mode & 2 && value; typeof current == 'object' && !~leafPrototypes.indexOf(current); current = getProto(current)) {
/******/ 			Object.getOwnPropertyNames(current).forEach((key) => (def[key] = () => (value[key])));
/******/ 		}
/******/ 		def['default'] = () => (value);
/******/ 		__nccwpck_require__.d(ns, def);
/******/ 		return ns;
/******/ 	};
/******/ })();
/******/ 
/******/ /* webpack/runtime/define property getters */
/******/ (() => {
/******/ 	// define getter functions for harmony exports
/******/ 	__nccwpck_require__.d = (exports, definition) => {
/******/ 		for(var key in definition) {
/******/ 			if(__nccwpck_require__.o(definition, key) && !__nccwpck_require__.o(exports, key)) {
/******/ 				Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 			}
/******/ 		}
/******/ 	};
/******/ })();
/******/ 
/******/ /* webpack/runtime/ensure chunk */
/******/ (() => {
/******/ 	__nccwpck_require__.f = {};
/******/ 	// This file contains only the entry chunk.
/******/ 	// The chunk loading function for additional chunks
/******/ 	__nccwpck_require__.e = (chunkId) => {
/******/ 		return Promise.all(Object.keys(__nccwpck_require__.f).reduce((promises, key) => {
/******/ 			__nccwpck_require__.f[key](chunkId, promises);
/******/ 			return promises;
/******/ 		}, []));
/******/ 	};
/******/ })();
/******/ 
/******/ /* webpack/runtime/get javascript chunk filename */
/******/ (() => {
/******/ 	// This function allow to reference async chunks
/******/ 	__nccwpck_require__.u = (chunkId) => {
/******/ 		// return url for filenames based on template
/******/ 		return "" + chunkId + ".index.js";
/******/ 	};
/******/ })();
/******/ 
/******/ /* webpack/runtime/hasOwnProperty shorthand */
/******/ (() => {
/******/ 	__nccwpck_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ })();
/******/ 
/******/ /* webpack/runtime/make namespace object */
/******/ (() => {
/******/ 	// define __esModule on exports
/******/ 	__nccwpck_require__.r = (exports) => {
/******/ 		if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 			Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 		}
/******/ 		Object.defineProperty(exports, '__esModule', { value: true });
/******/ 	};
/******/ })();
/******/ 
/******/ /* webpack/runtime/compat */
/******/ 
/******/ if (typeof __nccwpck_require__ !== 'undefined') __nccwpck_require__.ab = new URL('.', import.meta.url).pathname.slice(import.meta.url.match(/^file:\/\/\/\w:/) ? 1 : 0, -1) + "/";
/******/ 
/******/ /* webpack/runtime/import chunk loading */
/******/ (() => {
/******/ 	// no baseURI
/******/ 	
/******/ 	// object to store loaded and loading chunks
/******/ 	// undefined = chunk not loaded, null = chunk preloaded/prefetched
/******/ 	// [resolve, Promise] = chunk loading, 0 = chunk loaded
/******/ 	var installedChunks = {
/******/ 		792: 0
/******/ 	};
/******/ 	
/******/ 	var installChunk = (data) => {
/******/ 		var {ids, modules, runtime} = data;
/******/ 		// add "modules" to the modules object,
/******/ 		// then flag all "ids" as loaded and fire callback
/******/ 		var moduleId, chunkId, i = 0;
/******/ 		for(moduleId in modules) {
/******/ 			if(__nccwpck_require__.o(modules, moduleId)) {
/******/ 				__nccwpck_require__.m[moduleId] = modules[moduleId];
/******/ 			}
/******/ 		}
/******/ 		if(runtime) runtime(__nccwpck_require__);
/******/ 		for(;i < ids.length; i++) {
/******/ 			chunkId = ids[i];
/******/ 			if(__nccwpck_require__.o(installedChunks, chunkId) && installedChunks[chunkId]) {
/******/ 				installedChunks[chunkId][0]();
/******/ 			}
/******/ 			installedChunks[ids[i]] = 0;
/******/ 		}
/******/ 	
/******/ 	}
/******/ 	
/******/ 	__nccwpck_require__.f.j = (chunkId, promises) => {
/******/ 			// import() chunk loading for javascript
/******/ 			var installedChunkData = __nccwpck_require__.o(installedChunks, chunkId) ? installedChunks[chunkId] : undefined;
/******/ 			if(installedChunkData !== 0) { // 0 means "already installed".
/******/ 	
/******/ 				// a Promise means "currently loading".
/******/ 				if(installedChunkData) {
/******/ 					promises.push(installedChunkData[1]);
/******/ 				} else {
/******/ 					if(true) { // all chunks have JS
/******/ 						// setup Promise in chunk cache
/******/ 						var promise = import("./" + __nccwpck_require__.u(chunkId)).then(installChunk, (e) => {
/******/ 							if(installedChunks[chunkId] !== 0) installedChunks[chunkId] = undefined;
/******/ 							throw e;
/******/ 						});
/******/ 						var promise = Promise.race([promise, new Promise((resolve) => (installedChunkData = installedChunks[chunkId] = [resolve]))])
/******/ 						promises.push(installedChunkData[1] = promise);
/******/ 					}
/******/ 				}
/******/ 			}
/******/ 	};
/******/ 	
/******/ 	// no prefetching
/******/ 	
/******/ 	// no preloaded
/******/ 	
/******/ 	// no external install chunk
/******/ 	
/******/ 	// no on chunks loaded
/******/ })();
/******/ 
/************************************************************************/
var __webpack_exports__ = {};

// EXTERNAL MODULE: external "fs"
var external_fs_ = __nccwpck_require__(9896);
// EXTERNAL MODULE: external "path"
var external_path_ = __nccwpck_require__(6928);
;// CONCATENATED MODULE: external "os"
const external_os_namespaceObject = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("os");
;// CONCATENATED MODULE: ./src/x402_invoke.ts



function expandHomePath(inputPath) {
    if (inputPath === '~')
        return external_os_namespaceObject.homedir();
    if (inputPath.startsWith('~/'))
        return external_path_.join(external_os_namespaceObject.homedir(), inputPath.slice(2));
    return inputPath;
}
function findAgentWalletConfig() {
    const tronName = process.env.TRON_AGENT_WALLET_NAME;
    const evmName = process.env.EVM_AGENT_WALLET_NAME || process.env.BSC_AGENT_WALLET_NAME;
    const secretsDir = expandHomePath(process.env.AGENT_WALLET_SECRETS_DIR || '~/.agent-wallet');
    const password = process.env.AGENT_WALLET_PASSWORD || '';
    if (!tronName && !evmName) {
        // Check config files
        const configFiles = [
            external_path_.join(process.cwd(), 'x402-config.json'),
            external_path_.join(external_os_namespaceObject.homedir(), '.x402-config.json')
        ];
        for (const file of configFiles) {
            if (external_fs_.existsSync(file)) {
                try {
                    const config = JSON.parse(external_fs_.readFileSync(file, 'utf8'));
                    if (config.agent_wallet) {
                        return {
                            tronWalletName: config.agent_wallet.tron_wallet_name,
                            evmWalletName: config.agent_wallet.evm_wallet_name || config.agent_wallet.bsc_wallet_name,
                            secretsDir: expandHomePath(config.agent_wallet.secrets_dir || secretsDir),
                            password: config.agent_wallet.password || password,
                        };
                    }
                }
                catch (e) { /* ignore */ }
            }
        }
        return undefined;
    }
    return { tronWalletName: tronName, evmWalletName: evmName, secretsDir, password };
}
async function findPrivateKey(type) {
    // 1. Check environment variables
    if (type === 'tron') {
        if (process.env.TRON_PRIVATE_KEY)
            return process.env.TRON_PRIVATE_KEY;
    }
    else {
        if (process.env.EVM_PRIVATE_KEY)
            return process.env.EVM_PRIVATE_KEY;
        if (process.env.ETH_PRIVATE_KEY)
            return process.env.ETH_PRIVATE_KEY;
    }
    if (process.env.PRIVATE_KEY)
        return process.env.PRIVATE_KEY;
    // 2. Check local config files
    const configFiles = [
        external_path_.join(process.cwd(), 'x402-config.json'),
        external_path_.join(external_os_namespaceObject.homedir(), '.x402-config.json')
    ];
    for (const file of configFiles) {
        if (external_fs_.existsSync(file)) {
            try {
                const config = JSON.parse(external_fs_.readFileSync(file, 'utf8'));
                if (type === 'tron') {
                    const key = config.tron_private_key || config.private_key;
                    if (key)
                        return key;
                }
                else {
                    const key = config.evm_private_key || config.eth_private_key || config.private_key;
                    if (key)
                        return key;
                }
            }
            catch (e) { /* ignore */ }
        }
    }
    // 3. Check mcporter config
    const mcporterPath = external_path_.join(external_os_namespaceObject.homedir(), '.mcporter', 'mcporter.json');
    if (external_fs_.existsSync(mcporterPath)) {
        try {
            const config = JSON.parse(external_fs_.readFileSync(mcporterPath, 'utf8'));
            if (config.mcpServers) {
                for (const serverName in config.mcpServers) {
                    const s = config.mcpServers[serverName];
                    if (type === 'tron' && s?.env?.TRON_PRIVATE_KEY)
                        return s.env.TRON_PRIVATE_KEY;
                    if (type === 'evm' && (s?.env?.EVM_PRIVATE_KEY || s?.env?.ETH_PRIVATE_KEY)) {
                        return s.env.EVM_PRIVATE_KEY || s.env.ETH_PRIVATE_KEY;
                    }
                    if (s?.env?.PRIVATE_KEY)
                        return s.env.PRIVATE_KEY;
                }
            }
        }
        catch (e) { /* ignore */ }
    }
    return undefined;
}
async function findApiKey() {
    if (process.env.TRON_GRID_API_KEY)
        return process.env.TRON_GRID_API_KEY;
    const configFiles = [
        external_path_.join(process.cwd(), 'x402-config.json'),
        external_path_.join(external_os_namespaceObject.homedir(), '.x402-config.json')
    ];
    for (const file of configFiles) {
        if (external_fs_.existsSync(file)) {
            try {
                const config = JSON.parse(external_fs_.readFileSync(file, 'utf8'));
                const key = config.tron_grid_api_key || config.api_key;
                if (key)
                    return key;
            }
            catch (e) { /* ignore */ }
        }
    }
    const mcporterPath = external_path_.join(external_os_namespaceObject.homedir(), '.mcporter', 'mcporter.json');
    if (external_fs_.existsSync(mcporterPath)) {
        try {
            const config = JSON.parse(external_fs_.readFileSync(mcporterPath, 'utf8'));
            if (config.mcpServers) {
                for (const serverName in config.mcpServers) {
                    const s = config.mcpServers[serverName];
                    if (s?.env?.TRON_GRID_API_KEY)
                        return s.env.TRON_GRID_API_KEY;
                }
            }
        }
        catch (e) { /* ignore */ }
    }
    return undefined;
}
async function hasPrivateKeyConfig() {
    return Boolean((await findPrivateKey('tron')) || (await findPrivateKey('evm')));
}
function hasAgentWalletConfig(config) {
    return Boolean(config && Boolean(config.password));
}
async function main() {
    const args = process.argv.slice(2);
    const options = {};
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg.startsWith('--')) {
            const key = arg.slice(2);
            const value = args[i + 1];
            if (value && !value.startsWith('--')) {
                options[key] = value;
                i++;
            }
            else {
                options[key] = 'true';
            }
        }
    }
    const url = options.url;
    const entrypoint = options.entrypoint;
    const inputRaw = options.input;
    const methodArg = options.method;
    const networkName = options.network || 'nile';
    // Use dynamic imports
    // @ts-ignore
    const { TronWeb } = await __nccwpck_require__.e(/* import() */ 624).then(__nccwpck_require__.bind(__nccwpck_require__, 6624));
    global.TronWeb = TronWeb;
    const { TronClientSigner, EvmClientSigner, X402Client, X402FetchClient, ExactTronClientMechanism, ExactEvmClientMechanism, ExactPermitTronClientMechanism, ExactPermitEvmClientMechanism, AgentWalletAdapter, SufficientBalancePolicy } = await Promise.all(/* import() */[__nccwpck_require__.e(624), __nccwpck_require__.e(607), __nccwpck_require__.e(358)]).then(__nccwpck_require__.bind(__nccwpck_require__, 7358));
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
                if (agentWalletConfig.tronWalletName)
                    console.error(`[OK] TRON Agent Wallet: ${agentWalletConfig.tronWalletName}`);
                if (agentWalletConfig.evmWalletName)
                    console.error(`[OK] EVM Agent Wallet: ${agentWalletConfig.evmWalletName}`);
                console.error(`[OK] Secrets dir: ${agentWalletConfig.secretsDir}`);
            }
            else {
                console.error(`[WARN] No agent wallet configuration found.`);
            }
        }
        else {
            const tronKey = await findPrivateKey('tron');
            const evmKey = await findPrivateKey('evm');
            if (tronKey) {
                const signer = TronClientSigner.fromPrivateKey(tronKey);
                console.error(`[OK] TRON Wallet: ${signer.getAddress()}`);
                if (apiKey)
                    console.error(`[OK] TRON_GRID_API_KEY is configured.`);
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
        const awPassword = awConfigCandidate.password;
        if (!awPassword) {
            console.error('Error: AGENT_WALLET_PASSWORD is required for agent wallet mode.');
            process.exit(1);
        }
        const awConfig = awConfigCandidate;
        let WalletFactory;
        try {
            ({ WalletFactory } = await Promise.all(/* import() */[__nccwpck_require__.e(607), __nccwpck_require__.e(155)]).then(__nccwpck_require__.bind(__nccwpck_require__, 6155)));
        }
        catch {
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
    }
    else {
        // --- Private Key Mode ---
        const tronKey = await findPrivateKey('tron');
        const evmKey = await findPrivateKey('evm');
        if (tronKey) {
            const tronWebOptions = { fullHost: 'https://nile.trongrid.io', privateKey: tronKey };
            if (networkName === 'mainnet')
                tronWebOptions.fullHost = 'https://api.trongrid.io';
            if (networkName === 'shasta')
                tronWebOptions.fullHost = 'https://api.shasta.trongrid.io';
            if (apiKey)
                tronWebOptions.headers = { 'TRON-PRO-API-KEY': apiKey };
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
    let finalBody = undefined;
    if (entrypoint) {
        const baseUrl = url.endsWith('/') ? url.slice(0, -1) : url;
        finalUrl = `${baseUrl}/entrypoints/${entrypoint}/invoke`;
        finalMethod = 'POST';
        let inputData = {};
        if (inputRaw) {
            try {
                inputData = JSON.parse(inputRaw);
            }
            catch (e) {
                inputData = inputRaw;
            }
        }
        finalBody = JSON.stringify({ input: inputData });
    }
    else {
        if (methodArg)
            finalMethod = methodArg.toUpperCase();
        if (inputRaw)
            finalBody = inputRaw;
    }
    try {
        const fetchClient = new X402FetchClient(client);
        const requestInit = {
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
        }
        else if (contentType.includes('image/') || contentType.includes('application/octet-stream')) {
            const buffer = Buffer.from(await response.arrayBuffer());
            const tmpDir = external_os_namespaceObject.tmpdir();
            const isImage = contentType.includes('image/');
            const ext = isImage ? contentType.split('/')[1]?.split(';')[0] || 'bin' : 'bin';
            const fileName = `x402_${isImage ? 'image' : 'binary'}_${Date.now()}_${Math.random().toString(36).substring(7)}.${ext}`;
            const filePath = external_path_.join(tmpDir, fileName);
            external_fs_.writeFileSync(filePath, buffer);
            console.error(`[x402] Binary data saved to: ${filePath}`);
            responseBody = { file_path: filePath, content_type: contentType, bytes: buffer.length };
        }
        else {
            responseBody = await response.text();
        }
        process.stdout.write(JSON.stringify({
            status: response.status,
            headers: Object.fromEntries(response.headers.entries()),
            body: responseBody
        }, null, 2) + '\n');
    }
    catch (error) {
        let message = error.message || 'Unknown error';
        let stack = error.stack || '';
        // Sanitize any potential private key leaks in error messages/stacks
        const tronKey = await findPrivateKey('tron');
        const evmKey = await findPrivateKey('evm');
        const keys = [tronKey, evmKey].filter(Boolean);
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

