#!/usr/bin/env node
import { createRequire as __WEBPACK_EXTERNAL_createRequire } from "module";
/******/ var __webpack_modules__ = ({

/***/ 42613:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("assert");

/***/ }),

/***/ 20181:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("buffer");

/***/ }),

/***/ 76982:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("crypto");

/***/ }),

/***/ 24434:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("events");

/***/ }),

/***/ 79896:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("fs");

/***/ }),

/***/ 58611:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("http");

/***/ }),

/***/ 65692:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("https");

/***/ }),

/***/ 69278:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("net");

/***/ }),

/***/ 77598:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("node:crypto");

/***/ }),

/***/ 70857:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("os");

/***/ }),

/***/ 16928:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("path");

/***/ }),

/***/ 2203:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("stream");

/***/ }),

/***/ 64756:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("tls");

/***/ }),

/***/ 87016:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("url");

/***/ }),

/***/ 39023:
/***/ ((module) => {

module.exports = __WEBPACK_EXTERNAL_createRequire(import.meta.url)("util");

/***/ }),

/***/ 43106:
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
/******/ 		id: moduleId,
/******/ 		loaded: false,
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
/******/ 	// Flag the module as loaded
/******/ 	module.loaded = true;
/******/ 
/******/ 	// Return the exports of the module
/******/ 	return module.exports;
/******/ }
/******/ 
/******/ // expose the modules object (__webpack_modules__)
/******/ __nccwpck_require__.m = __webpack_modules__;
/******/ 
/************************************************************************/
/******/ /* webpack/runtime/compat get default export */
/******/ (() => {
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__nccwpck_require__.n = (module) => {
/******/ 		var getter = module && module.__esModule ?
/******/ 			() => (module['default']) :
/******/ 			() => (module);
/******/ 		__nccwpck_require__.d(getter, { a: getter });
/******/ 		return getter;
/******/ 	};
/******/ })();
/******/ 
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
/******/ /* webpack/runtime/node module decorator */
/******/ (() => {
/******/ 	__nccwpck_require__.nmd = (module) => {
/******/ 		module.paths = [];
/******/ 		if (!module.children) module.children = [];
/******/ 		return module;
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
/* harmony import */ var fs__WEBPACK_IMPORTED_MODULE_0__ = __nccwpck_require__(79896);
/* harmony import */ var fs__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__nccwpck_require__.n(fs__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var path__WEBPACK_IMPORTED_MODULE_1__ = __nccwpck_require__(16928);
/* harmony import */ var path__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__nccwpck_require__.n(path__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var os__WEBPACK_IMPORTED_MODULE_2__ = __nccwpck_require__(70857);
/* harmony import */ var os__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__nccwpck_require__.n(os__WEBPACK_IMPORTED_MODULE_2__);



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
        path__WEBPACK_IMPORTED_MODULE_1__.join(process.cwd(), 'x402-config.json'),
        path__WEBPACK_IMPORTED_MODULE_1__.join(os__WEBPACK_IMPORTED_MODULE_2__.homedir(), '.x402-config.json')
    ];
    for (const file of configFiles) {
        if (fs__WEBPACK_IMPORTED_MODULE_0__.existsSync(file)) {
            try {
                const config = JSON.parse(fs__WEBPACK_IMPORTED_MODULE_0__.readFileSync(file, 'utf8'));
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
    const mcporterPath = path__WEBPACK_IMPORTED_MODULE_1__.join(os__WEBPACK_IMPORTED_MODULE_2__.homedir(), '.mcporter', 'mcporter.json');
    if (fs__WEBPACK_IMPORTED_MODULE_0__.existsSync(mcporterPath)) {
        try {
            const config = JSON.parse(fs__WEBPACK_IMPORTED_MODULE_0__.readFileSync(mcporterPath, 'utf8'));
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
        path__WEBPACK_IMPORTED_MODULE_1__.join(process.cwd(), 'x402-config.json'),
        path__WEBPACK_IMPORTED_MODULE_1__.join(os__WEBPACK_IMPORTED_MODULE_2__.homedir(), '.x402-config.json')
    ];
    for (const file of configFiles) {
        if (fs__WEBPACK_IMPORTED_MODULE_0__.existsSync(file)) {
            try {
                const config = JSON.parse(fs__WEBPACK_IMPORTED_MODULE_0__.readFileSync(file, 'utf8'));
                const key = config.tron_grid_api_key || config.api_key;
                if (key)
                    return key;
            }
            catch (e) { /* ignore */ }
        }
    }
    const mcporterPath = path__WEBPACK_IMPORTED_MODULE_1__.join(os__WEBPACK_IMPORTED_MODULE_2__.homedir(), '.mcporter', 'mcporter.json');
    if (fs__WEBPACK_IMPORTED_MODULE_0__.existsSync(mcporterPath)) {
        try {
            const config = JSON.parse(fs__WEBPACK_IMPORTED_MODULE_0__.readFileSync(mcporterPath, 'utf8'));
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
    const { TronWeb } = await __nccwpck_require__.e(/* import() */ 270).then(__nccwpck_require__.bind(__nccwpck_require__, 52270));
    global.TronWeb = TronWeb;
    const { TronClientSigner, EvmClientSigner, X402Client, X402FetchClient, ExactTronClientMechanism, ExactEvmClientMechanism, ExactPermitTronClientMechanism, ExactPermitEvmClientMechanism, ExactGasFreeClientMechanism, SufficientBalancePolicy } = await Promise.all(/* import() */[__nccwpck_require__.e(270), __nccwpck_require__.e(667), __nccwpck_require__.e(914)]).then(__nccwpck_require__.bind(__nccwpck_require__, 68667));
    const tronKey = await findPrivateKey('tron');
    const evmKey = await findPrivateKey('evm');
    const apiKey = await findApiKey();
    if (options.check === 'true' || options.status === 'true') {
        if (tronKey) {
            const signer = new TronClientSigner(tronKey);
            console.error(`[OK] TRON Wallet: ${signer.getAddress()}`);
            if (apiKey)
                console.error(`[OK] TRON_GRID_API_KEY is configured.`);
        }
        if (evmKey) {
            const signer = new EvmClientSigner(evmKey);
            console.error(`[OK] EVM Wallet: ${signer.getAddress()}`);
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
        const tronWebOptions = { fullHost: 'https://nile.trongrid.io', privateKey: tronKey };
        if (networkName === 'mainnet')
            tronWebOptions.fullHost = 'https://api.trongrid.io';
        if (networkName === 'shasta')
            tronWebOptions.fullHost = 'https://api.shasta.trongrid.io';
        if (apiKey)
            tronWebOptions.headers = { 'TRON-PRO-API-KEY': apiKey };
        const tw = new TronWeb(tronWebOptions);
        const signer = new TronClientSigner(tronKey);
        const networks = ['mainnet', 'nile', 'shasta', '*'];
        for (const net of networks) {
            const networkId = net === '*' ? 'tron:*' : `tron:${net}`;
            client.register(networkId, new ExactTronClientMechanism(signer));
            client.register(networkId, new ExactPermitTronClientMechanism(signer));
            client.register(networkId, new ExactGasFreeClientMechanism(signer));
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
            const tmpDir = os__WEBPACK_IMPORTED_MODULE_2__.tmpdir();
            const isImage = contentType.includes('image/');
            const ext = isImage ? contentType.split('/')[1]?.split(';')[0] || 'bin' : 'bin';
            const fileName = `x402_${isImage ? 'image' : 'binary'}_${Date.now()}_${Math.random().toString(36).substring(7)}.${ext}`;
            const filePath = path__WEBPACK_IMPORTED_MODULE_1__.join(tmpDir, fileName);
            fs__WEBPACK_IMPORTED_MODULE_0__.writeFileSync(filePath, buffer);
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

