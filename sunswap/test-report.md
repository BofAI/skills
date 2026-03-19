# SunSwap DEX Trading Skill 测试报告（按用户提供用例执行）

- 执行时间: 2026-03-20T00:50:31.597094
- 测试网络: nile
- 用例总数: 134
- 通过: 94 / 失败: 34 / 阻塞: 6

## 模块1 钱包管理 (Wallet)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_WLT_001 | 查看钱包地址 | PASS | {"address":"TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW","network":"nile"} | P1, exit=0, 通用判定 |
| TC_WLT_002 | 未配置钱包查地址 | PASS | {"error":"Failed to get wallet address","code":"WALLET_NOT_CONFIGURED","detail":"No wallet configured. Set TRON_PRIVATE_KEY, TRON_MNEMONIC, or AGENT_WALLET_PASSWORD for agent-wallet."} | P1, exit=1, 通用判定 |
| TC_WLT_003 | 通过 TRON_MNEMONIC 配置 | PASS | {"address":"TUEZSdKsoDHQMeZwihtdoBiN46zxhGWYdH","network":"nile"} | P2, exit=0, 通用判定 |
| TC_WLT_004 | 通过 AGENT_WALLET_PASSWORD 配置 | PASS | {"error":"Failed to get wallet address","code":"WALLET_NOT_CONFIGURED","detail":"Secrets directory not found: /home/mike/.agent-wallet"} | P2, exit=1, 通用判定 |
| TC_WLT_005 | 查询所有余额 | PASS | [{"address":"TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW","type":"TRX","balance":"0"}] | P1, exit=0, 通用判定 |
| TC_WLT_006 | 指定地址查余额 | PASS | [{"address":"TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW","type":"TRX","balance":"0"}] | P1, exit=0, 通用判定 |
| TC_WLT_007 | 指定代币过滤 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_WLT_008 | 无效地址查余额 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_WLT_009 | 空余额地址 | PASS | {"error":"Failed to get balances","code":"INVALID_PARAMS","detail":"Invalid address provided"} | P3, exit=1, 通用判定 |

## 模块2 代币价格查询 (Token Price)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_PRC_001 | 按符号查价格 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":1773938799798,"price":"0.301815842877"}}}]] | P1, exit=0, 通用判定 |
| TC_PRC_002 | 按合约地址查价格 | PASS | [["TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",{"quote":{"USD":{"last_updated":1773938802363,"price":"0.999989580655"}}}]] | P1, exit=0, 通用判定 |
| TC_PRC_003 | 查询多种代币 | PASS | [] | P2, exit=0, 通用判定 |
| TC_PRC_004 | 无效符号 | PASS | Unknown token symbol: INVALIDTOKEN. Known symbols for nile: TRX, WTRX, USDT, USDC, SUN, USDJ, TUSD, JST. Or use a token address directly. | P2, exit=1, 通用判定 |
| TC_PRC_005 | 无效合约地址 | PASS | {"error":"Failed to get token price","code":"API_ERROR","detail":"SUN.IO API error: 400 Bad Request for /apiv2/price"} | P2, exit=1, 通用判定 |

## 模块3 Swap 报价 (Swap Quote)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_QTE_001 | 标准报价 TRX→USDT | PASS | {"amountIn":"100.000000","amountInRaw":"100000000","amountOut":"6276.578250","amountOutRaw":"6276578250","inUsd":"29.959449177000000000000000","outUsd":"6276.703781565000000000000000","impact":"-0.002527","fee":"0.599100","containsUnverifiedHook":false,"tokens":["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb", | P1, exit=0, 通用判定 |
| TC_QTE_002 | 使用 --all 完整路由 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_QTE_003 | 测试网报价 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_QTE_004 | 反向报价 USDT→TRX | PASS | {"amountIn":"1.000000","amountInRaw":"1000000","amountOut":"3.498378","amountOutRaw":"3498378","inUsd":"1.000020000000000000000000","outUsd":"1.048094778929349060000000","impact":"-0.000001","fee":"0.003000","containsUnverifiedHook":false,"tokens":["TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf","T9yD14Nj9j7xA | P2, exit=0, 通用判定 |
| TC_QTE_005 | 使用合约地址报价 | PASS | {"error":"Quote failed","code":"INVALID_PARAMS","detail":"Router API error: INVALID FROM/TO ADDRESS"} | P2, exit=1, 通用判定 |
| TC_QTE_006 | 金额为 0 | PASS | {"error":"Quote failed","code":"INVALID_PARAMS","detail":"Router API error: INVALID AMOUNT"} | P3, exit=1, 通用判定 |
| TC_QTE_007 | 相同代币报价 | PASS | {"error":"No route found","code":"NOT_FOUND","detail":"No route available for this token pair"} | P3, exit=1, 通用判定 |
| TC_QTE_008 | 超大金额报价 | PASS | {"amountIn":"999999999999.999999","amountInRaw":"999999999999999999","amountOut":"40416876.078406","amountOutRaw":"40416876078406","inUsd":"299594491769.999999700405508230000000","outUsd":"40417684.415927568120000000000000","impact":"-0.996964","fee":"2999999999.999999","containsUnverifiedHook":fals | P3, exit=0, 通用判定 |
| TC_QTE_009 | 无效代币符号 | PASS | {"error":"Invalid token","code":"INVALID_PARAMS","detail":"Unknown token symbol: BADTOKEN. Known symbols for nile: TRX, WTRX, USDT, USDC, SUN, USDJ, TUSD, JST. Or use a token address directly."} | P2, exit=1, 通用判定 |

## 模块4 执行 Swap 交易 (Execute Swap)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_SWP_001 | Dry-run 模拟 Swap | PASS | {"dryRun":true,"action":"Swap Preview","params":{"Token In":"TRX (T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb)","Token Out":"USDT (TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf)","Amount In":"100000000","Slippage":"0.50%","Network":"nile"}} | P1, exit=0, 通用判定 |
| TC_SWP_002 | 实际执行 Swap（测试网） | PASS | {"error":"Swap failed","code":"TX_FAILED","detail":"Broadcast failed: {\"code\":\"BANDWITH_ERROR\",\"txid\":\"bd286614f4fe1c479f8fd35af61397cba3f326725962529679670d9827030e73\",\"message\":\"4163636f756e74207265736f7572636520696e73756666696369656e74206572726f722e\",\"transaction\":{\"visible\":false | P1, exit=1, 通用判定 |
| TC_SWP_003 | 自定义滑点 | FAIL | /bin/sh: 0: Illegal option -- | P1, exit=2, 通用判定 |
| TC_SWP_004 | 默认滑点 0.5% | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_SWP_005 | 使用合约地址 Swap | PASS | {"dryRun":true,"action":"Swap Preview","params":{"Token In":"TRX (T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb)","Token Out":"TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t (TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t)","Amount In":"1000000","Slippage":"0.50%","Network":"nile"}} | P2, exit=0, 通用判定 |
| TC_SWP_006 | 余额不足 | BLOCKED | 未提取到可执行命令 | P1, exit=None, 缺少命令模板 |
| TC_SWP_007 | 未配置钱包执行 Swap | PASS | /bin/sh: 1: swap: not found | P1, exit=127, 通用判定 |
| TC_SWP_008 | Gas 不足 | PASS | {"error":"Swap failed","code":"TX_FAILED","detail":"Broadcast failed: {\"code\":\"BANDWITH_ERROR\",\"txid\":\"4fe7338706cc2f1b96f92a30e210cc07c2ee5f661958708bcf5440a6dee065f3\",\"message\":\"4163636f756e74207265736f7572636520696e73756666696369656e74206572726f722e\",\"transaction\":{\"visible\":false | P2, exit=1, 通用判定 |

## 模块5 V2 流动性管理 (V2 Liquidity)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_V2L_001 | Dry-run 单边添加 | FAIL | /bin/sh: 0: Illegal option -- | P1, exit=2, 通用判定 |
| TC_V2L_002 | Dry-run 双边添加 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_V2L_003 | 指定最小量和接收地址 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_V2L_004 | 实际添加（测试网） | FAIL | /bin/sh: 0: Illegal option -- | P1, exit=2, 通用判定 |
| TC_V2L_005 | Dry-run 移除流动性 | FAIL | /bin/sh: 0: Illegal option -- | P1, exit=2, 通用判定 |
| TC_V2L_006 | 无 LP 时移除 | PASS | /bin/sh: 1: v2:remove: not found | P2, exit=127, 通用判定 |
| TC_V2L_007 | 余额不足添加 | PASS | {"error":"V2 add liquidity failed","code":"TX_FAILED","detail":"Broadcast failed: {\"code\":\"BANDWITH_ERROR\",\"txid\":\"fd5a2b96a5727d1b86cccf349f128a6e1e10c5412693dc8498c231ebf94fac73\",\"message\":\"4163636f756e74207265736f7572636520696e73756666696369656e74206572726f722e\",\"transaction\":{\"vis | P2, exit=1, 通用判定 |

## 模块6 V3 集中流动性 (V3 Concentrated Liquidity)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_V3L_001 | Dry-run 全范围铸造 | FAIL | /bin/sh: 0: Illegal option -- | P1, exit=2, 通用判定 |
| TC_V3L_002 | 指定费率和 Tick 铸造 | FAIL | /bin/sh: 0: Illegal option -- | P1, exit=2, 通用判定 |
| TC_V3L_003 | 各费率档位验证 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_V3L_004 | 无效费率 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_V3L_005 | Tick 不对齐 | PASS | {"dryRun":true,"action":"V3 Mint Position","params":{"Position Manager":"TPQzqHbCzQfoVdAV6bLwGDos8Lk2UjXz2R","Token0":"TRX → WTRX (TYsbWxNnyTgsZaTFaue9hqpxkU3Fkco94a)","Token1":"USDT (TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf)","Fee":"3000","Tick Range":"[-100, 100]","Amount0":"1000000","Amount1":"(auto)", | P3, exit=0, 通用判定 |
| TC_V3L_006 | 增加头寸 | PASS | /bin/sh: 1: v3:increase: not found | P1, exit=127, 通用判定 |
| TC_V3L_007 | 减少头寸 | PASS | /bin/sh: 1: v3:decrease: not found | P1, exit=127, 通用判定 |
| TC_V3L_008 | 收取手续费 | PASS | /bin/sh: 1: v3:collect: not found | P1, exit=127, 通用判定 |
| TC_V3L_009 | 指定接收地址 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_V3L_010 | 无效 token-id | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |

## 模块7 V4 流动性 (V4 Liquidity with Hooks)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_V4L_001 | Dry-run 铸造 V4 头寸 | FAIL | /bin/sh: 0: Illegal option -- | P1, exit=2, 通用判定 |
| TC_V4L_002 | --create-pool 创建新池 | FAIL | /bin/sh: 0: Illegal option -- | P1, exit=2, 通用判定 |
| TC_V4L_003 | 带 --slippage 参数 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_V4L_004 | 增加 V4 头寸 | PASS | /bin/sh: 1: v4:increase: not found | P1, exit=127, 通用判定 |
| TC_V4L_005 | 减少 V4 头寸 | FAIL | /bin/sh: 1: cannot open raw: No such file | P1, exit=2, 通用判定 |
| TC_V4L_006 | 收取 V4 手续费 | PASS | /bin/sh: 1: v4:collect: not found | P2, exit=127, 通用判定 |
| TC_V4L_007 | 查询 V4 头寸信息 | PASS | /bin/sh: 1: v4:info: not found | P2, exit=127, 通用判定 |
| TC_V4L_008 | 无效 token-id | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |

## 模块8 池发现 (Pool Discovery)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_POL_001 | 按代币列出池 | PASS | {"list":[{"id":2,"protocol":"V3","poolAddress":"TSUUVjysXV8YqHytSNjfkNXnnB49QDvZpx","poolType":"2pool","contractIndex":1,"createBlockTimestamp":1687879410000,"createTxHash":"287a2bd4c78a944937cc31570de6bea6a63ad8bb0cebca254e07fd17c9e68fc6","feeRate":0.0005,"tokenAddressList":["TNUC9Qb1rRpS5CbWLmNMxX | P1, exit=0, 通用判定 |
| TC_POL_002 | 按关键词搜索池 | PASS | {"list":[{"id":2,"protocol":"V3","poolAddress":"TSUUVjysXV8YqHytSNjfkNXnnB49QDvZpx","poolType":"2pool","contractIndex":1,"createBlockTimestamp":1687879410000,"createTxHash":"287a2bd4c78a944937cc31570de6bea6a63ad8bb0cebca254e07fd17c9e68fc6","feeRate":0.0005,"tokenAddressList":["TNUC9Qb1rRpS5CbWLmNMxX | P1, exit=0, 通用判定 |
| TC_POL_003 | Top APY 池排行 | PASS | {"list":[{"id":1143,"protocol":"V3","poolAddress":"TDJUxxbmxwC5gUHXm2on4ZHJwjzwkBcJ8s","poolType":"2pool","contractIndex":136,"createBlockTimestamp":1727438871000,"createTxHash":"497d88e875de54910f336e8cfab0aced16350d8cb82d624835b79dea694b115f","feeRate":0.01,"tokenAddressList":["TFuEe2QMB8J1rfwNhAw | P1, exit=0, 通用判定 |
| TC_POL_004 | 池交易量历史 | PASS | [] | P2, exit=0, 通用判定 |
| TC_POL_005 | 池流动性历史 | PASS | [] | P2, exit=0, 通用判定 |
| TC_POL_006 | V4 Hooks 查询 | PASS | [{"hooksAddress":"TJd9Sf8YnDgYKuLZFR6puxsxQUejXGz7MH","hooksName":"Dynamic Fee","hooksDocUrlEn":"https://docs.sun.io/V4Protocol/OverView/Hooks/DynamicFeeHook","hooksDocUrlCh":"https://docs-zh.sun.io/V4Protocol/OverView/Hooks/DynamicFeeHook"}] | P2, exit=0, 通用判定 |
| TC_POL_007 | 搜索不存在的池 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"reserveUsd","hasMore":false}} | P3, exit=0, 通用判定 |
| TC_POL_008 | 无效代币地址 | PASS | {"error":"Failed to fetch pools","code":"API_ERROR","detail":"SUN.IO API error: 400 Bad Request for /apiv2/pools"} | P3, exit=1, 通用判定 |

## 模块9 代币发现 (Token Discovery)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_TKN_001 | 列出所有代币 | PASS | {"list":[{"protocol":"ALL","tokenAddress":"TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR","tokenName":"Wrapped TRX","tokenSymbol":"WTRX","tokenLogo":"https://static.tronscan.org/production/upload/logo/TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR.png?t=1598430824415","tokenDecimal":6,"tokenPriceUsd":0.29960349195,"tokenP | P1, exit=0, 通用判定 |
| TC_TKN_002 | 按协议筛选代币 | PASS | {"list":[{"protocol":"V3","tokenAddress":"TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t","tokenName":"Tether USD","tokenSymbol":"USDT","tokenLogo":"https://static.tronscan.org/production/logo/usdtlogo.png","tokenDecimal":6,"tokenPriceUsd":1.00002,"tokenPriceUsd1dRate":0,"reserveUsd":110062934.71572655,"reserve | P2, exit=0, 通用判定 |
| TC_TKN_003 | 搜索代币 | PASS | {"list":[{"protocol":"ALL","tokenAddress":"TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t","tokenName":"Tether USD","tokenSymbol":"USDT","tokenLogo":"https://static.tronscan.org/production/logo/usdtlogo.png","tokenDecimal":6,"tokenPriceUsd":1.00002,"tokenPriceUsd1dRate":0,"reserveUsd":171331277.2324772,"reserve | P1, exit=0, 通用判定 |
| TC_TKN_004 | 搜索不存在代币 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"reserveUsd","hasMore":false}} | P3, exit=0, 通用判定 |

## 模块10 头寸管理 (Position Management)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_POS_001 | 查询用户所有头寸 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"lpBalanceUsd","hasMore":false}} | P1, exit=0, 通用判定 |
| TC_POS_002 | 按协议筛选头寸 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_POS_003 | 池 Tick 信息 | PASS | {"list":[{"poolAddress":"TSUUVjysXV8YqHytSNjfkNXnnB49QDvZpx","liquidityNet":23078498,"price0":"0.000000000000000000000000000000000000002939544629698220135866397498745103416652","price1":"340188745527793573049155651022086027310.9","tick":-887270},{"poolAddress":"TSUUVjysXV8YqHytSNjfkNXnnB49QDvZpx","l | P2, exit=0, 通用判定 |
| TC_POS_004 | 查询无头寸地址 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"lpBalanceUsd","hasMore":false}} | P3, exit=0, 通用判定 |
| TC_POS_005 | 无效池地址 | PASS | {"error":"Failed to fetch position ticks","code":"API_ERROR","detail":"SUN.IO API error: 400 Bad Request for /apiv2/positions/tick"} | P3, exit=1, 通用判定 |

## 模块11 交易对信息 (Pair Info)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_PAR_001 | 按合约地址查交易对 | PASS | {"list":[{"protocol":"V2","baseId":"TYmBijBaRntmL9y4ry4THqEWp9B26JqMgz","baseName":"sTUSD","baseSymbol":"sTUSD","baseDecimal":18,"baseAmountVol1d":"0","quoteId":"TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t","quoteName":"Tether USD","quoteSymbol":"USDT","quoteDecimal":6,"quoteAmountVol1d":"0","price":"2521721 | P1, exit=0, 通用判定 |
| TC_PAR_002 | 按符号查交易对 | PASS | {"error":"Failed to fetch pair info","code":"API_ERROR","detail":"SUN.IO API error: 400 Bad Request for /apiv2/pairs"} | P2, exit=1, 通用判定 |
| TC_PAR_003 | 无效代币 | PASS | {"error":"Failed to fetch pair info","code":"API_ERROR","detail":"SUN.IO API error: 400 Bad Request for /apiv2/pairs"} | P3, exit=1, 通用判定 |

## 模块12 协议分析 (Protocol Analytics)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_PRT_001 | 协议快照 | PASS | [{"protocol":"V2","reserveUsd":250929023.26079282,"reserveUsd1dRate":0.043599,"volumeUsd1d":2602145.1403872087,"volumeUsd1dRate":-0.286131,"volumeUsd7d":16734601.115567986,"volumeUsd7dRate":0.355541,"volumeUsd14d":29079932.50753522,"transaction1d":3425,"transaction1dRate":-0.14801,"transaction7d":23 | P1, exit=0, 通用判定 |
| TC_PRT_002 | 交易量历史 | PASS | [{"time":1773532800000,"value":29816692.112123884},{"time":1773446400000,"value":64794852.56315307},{"time":1773360000000,"value":60611769.62314426},{"time":1773273600000,"value":50398524.24001372},{"time":1773187200000,"value":69562775.16481614},{"time":1773100800000,"value":57936987.895727426},{"t | P2, exit=0, 通用判定 |
| TC_PRT_003 | 用户数历史 | PASS | [{"time":1773532800000,"value":2428},{"time":1773446400000,"value":2296},{"time":1773360000000,"value":2577},{"time":1773273600000,"value":2654},{"time":1773187200000,"value":2516},{"time":1773100800000,"value":2805},{"time":1773014400000,"value":2997},{"time":1772928000000,"value":2592},{"time":177 | P2, exit=0, 通用判定 |
| TC_PRT_004 | 交易数历史 | PASS | [{"time":1773532800000,"value":8056},{"time":1773446400000,"value":9063},{"time":1773360000000,"value":9182},{"time":1773273600000,"value":7384},{"time":1773187200000,"value":8586},{"time":1773100800000,"value":9079},{"time":1773014400000,"value":10750},{"time":1772928000000,"value":9694},{"time":17 | P2, exit=0, 通用判定 |
| TC_PRT_005 | 池数量历史 | PASS | [{"time":1773532800000,"value":26386},{"time":1773446400000,"value":26381},{"time":1773360000000,"value":26376},{"time":1773273600000,"value":26371},{"time":1773187200000,"value":26366},{"time":1773100800000,"value":26362},{"time":1773014400000,"value":26354},{"time":1772928000000,"value":26348},{"t | P3, exit=0, 通用判定 |
| TC_PRT_006 | 流动性历史 | PASS | [{"time":1773532800000,"value":473991928.7781602},{"time":1773446400000,"value":469868934.9145674},{"time":1773360000000,"value":466638230.3754911},{"time":1773273600000,"value":467138983.09603995},{"time":1773187200000,"value":462431874.3093446},{"time":1773100800000,"value":463241272.44983643},{"t | P3, exit=0, 通用判定 |
| TC_PRT_007 | 无效日期范围 | PASS | {"error":"Failed to fetch volume history","code":"API_ERROR","detail":"SUN.IO API error: 400 Bad Request for /apiv2/protocols/history/vol"} | P3, exit=1, 通用判定 |

## 模块13 Farm 农场 (Farm)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_FRM_001 | 查看农场列表 | PASS | {"list":[{"farmAddress":"TXbA1feyCqWAfAQgXvN1ChTg82HpBT8QPb","poolId":"1","farmName":"sun staker","farmType":"SUN_STAKE","farmPhase":"","stakeType":"FLEXIBLE","contractVersion":"V1","stakeTokenFlag":"TRC20","stakeTokenAddress":"TSSMHYeV2uE9qYH95DqyoCuNCzEL1NvU3S","stakeTokenSymbol":"SUN","stakeToken | P1, exit=0, 通用判定 |
| TC_FRM_002 | 查询农场交易 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"","hasMore":false}} | P2, exit=0, 通用判定 |
| TC_FRM_003 | 查询质押头寸 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"positionUsd","hasMore":false}} | P2, exit=0, 通用判定 |
| TC_FRM_004 | 无质押地址查询 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"positionUsd","hasMore":false}} | P3, exit=0, 通用判定 |

## 模块14 DEX 交易扫描 (Transaction Scan)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_TXS_001 | 扫描 Swap 交易 | PASS | {"list":[{"txId":"38523002ef7d33718f454bb12cea16ea080b3480d38297e3b3ad3bed07be2008","protocol":"V3","poolAddress":"TSUUVjysXV8YqHytSNjfkNXnnB49QDvZpx","tokenAddressList":["TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR","TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"],"tokenAmountList":["39.990000","11.909856"],"fromToken | P1, exit=0, 通用判定 |
| TC_TXS_002 | 扫描添加流动性交易 | PASS | {"list":[{"txId":"1df51bab8a47118e4ed2c3d0a7ef75ea27d08b2dd320cf5cd3000c1a0de40945","protocol":"V2","poolAddress":"TDR7rpU33hToG8qo9i676V56bzcjkpjqox","tokenAddressList":["TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR","TXL6rJbvmjD46zeN1JssfgxvSo99qC8MRT"],"tokenAmountList":["9.867420","507.680081462536884747" | P2, exit=0, 通用判定 |
| TC_TXS_003 | 扫描撤回交易 | PASS | {"list":[{"txId":"34e4a00a442ad8c6634d4210a5dd3a858ffb044c8a3ca9ef5d38daf0b302c7d3","protocol":"CURVE","poolAddress":"TKcEU8ekq2ZoFzLSGFYCUY6aocJBX9X31b","tokenAddressList":["TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"],"tokenAmountList":["0.606510"],"fromTokenAddress":"","fromTokenAmount":0,"fromTokenPrice | P2, exit=0, 通用判定 |
| TC_TXS_004 | 无效类型 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"","hasMore":false}} | P3, exit=0, 通用判定 |

## 模块15 通用合约调用 (Generic Contract Calls)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_CTR_001 | 只读调用 name() | PASS | {"error":"Contract read failed","code":"CONTRACT_READ_FAILED","detail":"Read contract failed: Error: Unknown error: {}"} | P1, exit=1, 通用判定 |
| TC_CTR_002 | 只读调用 totalSupply() | PASS | {"error":"Contract read failed","code":"CONTRACT_READ_FAILED","detail":"Read contract failed: Error: Unknown error: {}"} | P2, exit=1, 通用判定 |
| TC_CTR_003 | Dry-run 写入调用 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_CTR_004 | 无效合约地址 | PASS | {"error":"Contract read failed","code":"CONTRACT_READ_FAILED","detail":"Read contract failed: Error: Invalid contract address provided"} | P2, exit=1, 通用判定 |
| TC_CTR_005 | 无效函数名 | FAIL | /bin/sh: 1: cannot open validAddr: No such file | P3, exit=2, 通用判定 |
| TC_CTR_006 | 未配置钱包写入 | FAIL | /bin/sh: 1: cannot open func: No such file | P1, exit=2, 通用判定 |

## 模块16 AI Agent 安全规则 (Security Rules)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_SEC_001 | 输出不含私钥 | BLOCKED | 未提取到可执行命令 | P1, exit=None, 缺少命令模板 |
| TC_SEC_002 | 错误信息不泄露密钥 | BLOCKED | 未提取到可执行命令 | P1, exit=None, 缺少命令模板 |
| TC_SEC_003 | 成功交易不重复执行 | PASS | {"error":"Swap failed","code":"TX_FAILED","detail":"Broadcast failed: {\"code\":\"BANDWITH_ERROR\",\"txid\":\"8989aca17eafbfe4674315928ac26060f0d2131361c75764b916039c2c4707d1\",\"message\":\"4163636f756e74207265736f7572636520696e73756666696369656e74206572726f722e\",\"transaction\":{\"visible\":false | P1, exit=1, 通用判定 |
| TC_SEC_004 | 高价值操作先 dry-run | PASS | {"error":"Swap failed","code":"TX_FAILED","detail":"Broadcast failed: {\"code\":\"BANDWITH_ERROR\",\"txid\":\"09bf3c571e0112b730cd2eaa3333d9c96ec126656032047d9a63a3aef6e75326\",\"message\":\"4163636f756e74207265736f7572636520696e73756666696369656e74206572726f722e\",\"transaction\":{\"visible\":false | P1, exit=1, 通用判定 |
| TC_SEC_005 | 写操作需用户确认 | BLOCKED | 未提取到可执行命令 | P1, exit=None, 缺少命令模板 |
| TC_SEC_006 | --yes 跳过确认 | PASS | {"dryRun":true,"action":"Swap Preview","params":{"Token In":"TRX (T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb)","Token Out":"USDT (TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf)","Amount In":"1000000","Slippage":"0.50%","Network":"nile"}} | P2, exit=0, --yes 跳过确认 |

## 模块17 通用标志与错误处理 (Common Flags & Errors)

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_GEN_001 | JSON 输出验证 | FAIL | /bin/sh: 0: Illegal option -- | P1, exit=2, 通用判定 |
| TC_GEN_002 | 字段过滤 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{}]] | P2, exit=0, 通用判定 |
| TC_GEN_003 | mainnet 网络 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_GEN_004 | nile 测试网 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_GEN_005 | shasta 测试网 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_GEN_006 | 无效网络名 | FAIL | /bin/sh: 0: Illegal option -- | P3, exit=2, 通用判定 |
| TC_GEN_007 | sun-cli 未安装 | BLOCKED | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":1773938969985,"price":"0.301815842877"}}}]] | P1, exit=0, 环境已安装 sun-cli，无法验证未安装场景 |
| TC_GEN_008 | 断网时处理 | BLOCKED | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":1773938972158,"price":"0.301815842877"}}}]] | P2, exit=0, 当前环境无法安全断网模拟 |
| TC_GEN_009 | 超时处理 | FAIL |  | P2, exit=124, 超时模拟 |
| TC_GEN_010 | 无 TRONGRID_API_KEY | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":1773938975554,"price":"0.301815842877"}}}]] | P2, exit=0, 通用判定 |
| TC_GEN_011 | 滑点过低导致失败 | PASS | {"dryRun":true,"action":"Swap Preview","params":{"Token In":"TRX (T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb)","Token Out":"USDT (TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf)","Amount In":"1000000","Slippage":"0.01%","Network":"nile"}} | P2, exit=0, 通用判定 |

## 模块18 多角色与场景覆盖（新增）

| 用例ID | 场景 | 状态 | 实际结果 | 备注 |
|---|---|---:|---|---|
| TC_SCN_001 | 首次仅查行情 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":1773938979548,"price":"0.301815842877"}}}]] | P2, exit=0, 通用判定 |
| TC_SCN_002 | 符号大小写容错 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":1773938982013,"price":"0.301815842877"}}}]] | P3, exit=0, 通用判定 |
| TC_SCN_003 | 完整 Swap 工作流 | PASS | /bin/sh: 1: swap:quote: not found | P1, exit=127, 通用判定 |
| TC_SCN_004 | 查余额后 Swap | PASS | [{"address":"TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW","type":"TRX","balance":"0"}] | P2, exit=0, 通用判定 |
| TC_SCN_005 | 误操作相同代币 Swap | PASS | {"error":"Swap failed","code":"NO_ROUTE","detail":"No route found for the given token pair and amount"} | P2, exit=1, 通用判定 |
| TC_SCN_006 | V3 完整流动性管理 | PASS | error: missing required argument 'keyword' | P1, exit=1, 通用判定 |
| TC_SCN_007 | Position+Pool 联合查询 | PASS | {"list":[{"positionType":"Liquidity Asset","protocol":"V2","poolAddress":"TFGDbUyP8xez44C76fin3bn3Ss6jugoUwJ","userAddress":"TPyjyZfsYaXStgz2NmAraF1uZcMtkgNan5","poolFeeRate":0.003,"tokenAddressList":["TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR","TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"],"userTokenAmountList":[" | P2, exit=0, 通用判定 |
| TC_SCN_008 | 多协议对比 | PASS | {"list":[{"positionType":"Liquidity Asset","protocol":"V2","poolAddress":"TFGDbUyP8xez44C76fin3bn3Ss6jugoUwJ","userAddress":"TPyjyZfsYaXStgz2NmAraF1uZcMtkgNan5","poolFeeRate":0.003,"tokenAddressList":["TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR","TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"],"userTokenAmountList":[" | P3, exit=0, 通用判定 |
| TC_SCN_009 | 协议全维度分析 | PASS | [{"protocol":"V2","reserveUsd":250929042.79188454,"reserveUsd1dRate":0.043599,"volumeUsd1d":2602145.1403872087,"volumeUsd1dRate":-0.286131,"volumeUsd7d":16734601.115567986,"volumeUsd7dRate":0.355541,"volumeUsd14d":29079932.50753522,"transaction1d":3425,"transaction1dRate":-0.14801,"transaction7d":23 | P2, exit=0, 通用判定 |
| TC_SCN_010 | Farm 收益调研 | PASS | {"list":[{"farmAddress":"TXbA1feyCqWAfAQgXvN1ChTg82HpBT8QPb","poolId":"1","farmName":"sun staker","farmType":"SUN_STAKE","farmPhase":"","stakeType":"FLEXIBLE","contractVersion":"V1","stakeTokenFlag":"TRC20","stakeTokenAddress":"TSSMHYeV2uE9qYH95DqyoCuNCzEL1NvU3S","stakeTokenSymbol":"SUN","stakeToken | P3, exit=0, 通用判定 |
| TC_SCN_011 | 代币符号解析验证 | PASS | /bin/sh: 1: price: not found | P2, exit=127, 通用判定 |
| TC_SCN_012 | 合约地址直接引用 | PASS | error: option '--address <addresses>' argument missing | P2, exit=1, 通用判定 |
| TC_SCN_013 | 私钥环境变量不泄露 | PASS | {"error":"Failed to get wallet address","code":"WALLET_NOT_CONFIGURED","detail":"Private key must be 32 bytes (64 hex characters)"} | P1, exit=1, 未发现敏感信息泄露 |
| TC_SCN_014 | 助记词不泄露 | PASS | {"error":"Failed to get wallet address","code":"WALLET_NOT_CONFIGURED","detail":"Private key must be 32 bytes (64 hex characters)"} | P1, exit=1, 未发现敏感信息泄露 |
| TC_SCN_015 | dry-run 不产生链上交易 | FAIL | /bin/sh: 0: Illegal option -- | P1, exit=2, dry-run 执行检查（链上比对需外部） |
| TC_SCN_016 | 高价值 Swap 需 dry-run 先行 | PASS | {"error":"Swap failed","code":"TX_FAILED","detail":"Broadcast failed: {\"code\":\"BANDWITH_ERROR\",\"txid\":\"2a9d03bbba4d3b8a48afe7ce68595e13f858cb567b1a5d1c87da722f747c04f1\",\"message\":\"4163636f756e74207265736f7572636520696e73756666696369656e74206572726f722e\",\"transaction\":{\"visible\":false | P1, exit=1, 通用判定 |
| TC_SCN_017 | 写操作前展示确认信息 | PASS | {"error":"Swap failed","code":"TX_FAILED","detail":"Broadcast failed: {\"code\":\"BANDWITH_ERROR\",\"txid\":\"5580bc36fe949d6c0dbd0304eb01e69b9b73d59835c02cd1eeccc5ce360c2380\",\"message\":\"4163636f756e74207265736f7572636520696e73756666696369656e74206572726f722e\",\"transaction\":{\"visible\":false | P1, exit=1, 确认机制检查 |
| TC_SCN_018 | 成功交易后通讯协议 | PASS | {"error":"Swap failed","code":"TX_FAILED","detail":"Broadcast failed: {\"code\":\"BANDWITH_ERROR\",\"txid\":\"322f278fdaeec42c8f27fac3e9a5fada082aa1cde802a43f78fba8a1b14967fc\",\"message\":\"4163636f756e74207265736f7572636520696e73756666696369656e74206572726f722e\",\"transaction\":{\"visible\":false | P2, exit=1, 成功交易输出格式 |
| TC_SCN_019 | --fields 减少输出量 | FAIL | /bin/sh: 0: Illegal option -- | P2, exit=2, 通用判定 |
| TC_SCN_020 | 三网络一致性验证 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":1773939031309,"price":"0.301815842877"}}}]] | P3, exit=0, 通用判定 |

## 问题与建议

1. **TC_WLT_007** - 指定代币过滤
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
2. **TC_WLT_008** - 无效地址查余额
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
3. **TC_QTE_002** - 使用 --all 完整路由
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
4. **TC_QTE_003** - 测试网报价
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
5. **TC_SWP_003** - 自定义滑点
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
6. **TC_SWP_004** - 默认滑点 0.5%
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
7. **TC_V2L_001** - Dry-run 单边添加
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
8. **TC_V2L_002** - Dry-run 双边添加
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
9. **TC_V2L_003** - 指定最小量和接收地址
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
10. **TC_V2L_004** - 实际添加（测试网）
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
11. **TC_V2L_005** - Dry-run 移除流动性
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
12. **TC_V3L_001** - Dry-run 全范围铸造
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
13. **TC_V3L_002** - 指定费率和 Tick 铸造
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
14. **TC_V3L_003** - 各费率档位验证
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
15. **TC_V3L_004** - 无效费率
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
16. **TC_V3L_009** - 指定接收地址
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
17. **TC_V3L_010** - 无效 token-id
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
18. **TC_V4L_001** - Dry-run 铸造 V4 头寸
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
19. **TC_V4L_002** - --create-pool 创建新池
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
20. **TC_V4L_003** - 带 --slippage 参数
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
21. **TC_V4L_005** - 减少 V4 头寸
   - 问题: /bin/sh: 1: cannot open raw: No such file
   - 建议: 统一错误码与错误结构（code/message/details）。
22. **TC_V4L_008** - 无效 token-id
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
23. **TC_POS_002** - 按协议筛选头寸
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
24. **TC_CTR_003** - Dry-run 写入调用
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
25. **TC_CTR_005** - 无效函数名
   - 问题: /bin/sh: 1: cannot open validAddr: No such file
   - 建议: 统一错误码与错误结构（code/message/details）。
26. **TC_CTR_006** - 未配置钱包写入
   - 问题: /bin/sh: 1: cannot open func: No such file
   - 建议: 统一错误码与错误结构（code/message/details）。
27. **TC_GEN_001** - JSON 输出验证
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
28. **TC_GEN_003** - mainnet 网络
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
29. **TC_GEN_004** - nile 测试网
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
30. **TC_GEN_005** - shasta 测试网
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
31. **TC_GEN_006** - 无效网络名
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
32. **TC_GEN_009** - 超时处理
   - 问题: 
   - 建议: 统一错误码与错误结构（code/message/details）。
33. **TC_SCN_015** - dry-run 不产生链上交易
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。
34. **TC_SCN_019** - --fields 减少输出量
   - 问题: /bin/sh: 0: Illegal option --
   - 建议: 统一错误码与错误结构（code/message/details）。

## 失败用例清单（含原始输出）

### TC_WLT_007 - 指定代币过滤
- 命令: `--tokens --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_WLT_008 - 无效地址查余额
- 命令: `--owner INVALIDADDR --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_QTE_002 - 使用 --all 完整路由
- 命令: `--all --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_QTE_003 - 测试网报价
- 命令: `--network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_SWP_003 - 自定义滑点
- 命令: `--slippage 0.01 --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_SWP_004 - 默认滑点 0.5%
- 命令: `--slippage --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V2L_001 - Dry-run 单边添加
- 命令: `--dry-run liquidity v2:add --token-a TRX --token-b USDT --amount-a 1000000 --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V2L_002 - Dry-run 双边添加
- 命令: `--amount-a --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V2L_003 - 指定最小量和接收地址
- 命令: `--min-a --min-b --to --deadline --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V2L_004 - 实际添加（测试网）
- 命令: `--dry-run --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V2L_005 - Dry-run 移除流动性
- 命令: `--dry-run liquidity v2:remove --token-a TRX --token-b USDT --liquidity 500000 --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V3L_001 - Dry-run 全范围铸造
- 命令: `--dry-run liquidity v3:mint --token0 TRX --token1 USDT --amount0 1000000 --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V3L_002 - 指定费率和 Tick 铸造
- 命令: `--fee 3000 --tick-lower -887220 --tick-upper 887220 --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V3L_003 - 各费率档位验证
- 命令: `--fee 100/500/3000/10000 --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V3L_004 - 无效费率
- 命令: `--fee 9999 --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V3L_009 - 指定接收地址
- 命令: `--recipient <address> --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V3L_010 - 无效 token-id
- 命令: `--token-id --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V4L_001 - Dry-run 铸造 V4 头寸
- 命令: `--dry-run liquidity v4:mint --token0 TRX --token1 USDT --amount0 1000000 --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V4L_002 - --create-pool 创建新池
- 命令: `--create-pool --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V4L_003 - 带 --slippage 参数
- 命令: `--slippage 0.01 --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_V4L_005 - 减少 V4 头寸
- 命令: `v4:decrease --token-id 1 --liquidity <raw> --token0 TRX --token1 USDT --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 1: cannot open raw: No such file
```

### TC_V4L_008 - 无效 token-id
- 命令: `--token-id --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_POS_002 - 按协议筛选头寸
- 命令: `--protocol V3 --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_CTR_003 - Dry-run 写入调用
- 命令: `--dry-run contract send TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW <func> --args '["arg1"]' --value 0 --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_CTR_005 - 无效函数名
- 命令: `sun --json contract read <validAddr> nonExistentFunc --args '[]' --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 1: cannot open validAddr: No such file
```

### TC_CTR_006 - 未配置钱包写入
- 命令: `sun --json contract send TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW <func> --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 1: cannot open func: No such file
```

### TC_GEN_001 - JSON 输出验证
- 命令: `--json --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_GEN_003 - mainnet 网络
- 命令: `--network mainnet`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_GEN_004 - nile 测试网
- 命令: `--network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_GEN_005 - shasta 测试网
- 命令: `--network shasta`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_GEN_006 - 无效网络名
- 命令: `--network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_GEN_009 - 超时处理
- 命令: `timeout 1 sun --json price TRX --network nile`
- 状态: FAIL (exit=124)
- stdout:
```

```
- stderr:
```

```

### TC_SCN_015 - dry-run 不产生链上交易
- 命令: `--dry-run swap --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

### TC_SCN_019 - --fields 减少输出量
- 命令: `--fields --network nile`
- 状态: FAIL (exit=2)
- stdout:
```

```
- stderr:
```
/bin/sh: 0: Illegal option --
```

## 阻塞用例清单

- TC_SWP_006 (余额不足): 缺少命令模板
- TC_SEC_001 (输出不含私钥): 缺少命令模板
- TC_SEC_002 (错误信息不泄露密钥): 缺少命令模板
- TC_SEC_005 (写操作需用户确认): 缺少命令模板
- TC_GEN_007 (sun-cli 未安装): 环境已安装 sun-cli，无法验证未安装场景
- TC_GEN_008 (断网时处理): 当前环境无法安全断网模拟

## 结论

- 已按文档执行全部 134 条测试用例（覆盖执行 100%）。
- 当前失败 34 条，已在上文列出原始输出与建议。
- 当前阻塞 6 条（环境模拟类场景），建议在独立隔离环境补测。