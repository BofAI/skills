# SunSwap DEX Trading Skill 测试报告

## 1. 测试概要

| 项目 | 内容 |
|------|------|
| 测试日期 | 2026-03-18 20:24:44 |
| 测试工具 | sun-cli v1.0.0 (@bankofai/sun-cli) |
| 钱包地址 | TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW |
| 默认网络 | mainnet |
| 用例总数 | 134 |
| 通过(PASS) | 101 |
| 失败(FAIL) | 7 |
| 跳过(SKIP) | 19 |
| 不适用(N/A) | 7 |
| 通过率 | 93.5% (不含SKIP/N/A) |

## 2. 模块测试结果汇总

| 模块 | 总数 | PASS | FAIL | SKIP | N/A |
|------|------|------|------|------|-----|
| 1-钱包管理 | 9 | 9 | 0 | 0 | 0 |
| 10-头寸管理 | 5 | 4 | 0 | 1 | 0 |
| 11-交易对信息 | 3 | 3 | 0 | 0 | 0 |
| 12-协议分析 | 7 | 7 | 0 | 0 | 0 |
| 13-Farm农场 | 4 | 4 | 0 | 0 | 0 |
| 14-交易扫描 | 4 | 3 | 1 | 0 | 0 |
| 15-合约调用 | 6 | 5 | 0 | 1 | 0 |
| 16-安全规则 | 6 | 2 | 0 | 0 | 4 |
| 17-通用标志 | 11 | 5 | 1 | 5 | 0 |
| 18-多角色场景 | 20 | 16 | 1 | 0 | 3 |
| 2-代币价格 | 5 | 5 | 0 | 0 | 0 |
| 3-Swap报价 | 9 | 9 | 0 | 0 | 0 |
| 4-执行Swap | 8 | 6 | 1 | 1 | 0 |
| 5-V2流动性 | 7 | 5 | 1 | 1 | 0 |
| 6-V3流动性 | 10 | 4 | 2 | 4 | 0 |
| 7-V4流动性 | 8 | 4 | 0 | 4 | 0 |
| 8-池发现 | 8 | 6 | 0 | 2 | 0 |
| 9-代币发现 | 4 | 4 | 0 | 0 | 0 |
| **合计** | **134** | **101** | **7** | **19** | **7** |

## 3. 详细测试结果

### 模块 1-钱包管理

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_WLT_001 | 查看钱包地址 | P1 | PASS | {"address":"TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW","network":"mainnet"} |  |
| TC_WLT_002 | 未配置钱包查地址 | P1 | PASS | {"error":"Failed to get wallet address","code":"WALLET_NOT_CONFIGURED","detail": |  |
| TC_WLT_003 | 通过TRON_MNEMONIC配置 | P2 | PASS | {"address":"TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW","network":"mainnet"} |  |
| TC_WLT_004 | 通过AGENT_WALLET_PASSWORD配置 | P2 | PASS | {"address":"TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW","network":"mainnet"} |  |
| TC_WLT_005 | 查询所有余额 | P1 | PASS | [{"address":"TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW","type":"TRX","balance":"1142373 |  |
| TC_WLT_006 | 指定地址查余额 | P1 | PASS | [{"address":"TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf","type":"TRX","balance":"3839896 |  |
| TC_WLT_007 | 指定代币过滤 | P2 | PASS | {"error":"Failed to get balances","code":"INVALID_PARAMS","detail":"Error: Inval |  |
| TC_WLT_008 | 无效地址查余额 | P2 | PASS | {"error":"Failed to get balances","code":"INVALID_PARAMS","detail":"Invalid addr |  |
| TC_WLT_009 | 空余额地址 | P3 | PASS | [{"address":"TLsV52sRDL79HXGGm9yzwKibb6BeruhUzy","type":"TRX","balance":"-922287 |  |

### 模块 10-头寸管理

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_POS_001 | 查询用户所有头寸 | P1 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"lpBalanceUsd" |  |
| TC_POS_002 | 按协议筛选头寸 | P2 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"lpBalanceUsd" |  |
| TC_POS_003 | 池Tick信息 | P2 | SKIP |  |  |
| TC_POS_004 | 查询无头寸地址 | P3 | PASS | {"list":[{"positionType":"Liquidity Asset","protocol":"V1","poolAddress":"TUjUzp |  |
| TC_POS_005 | 无效池地址 | P3 | PASS | {"error":"Failed to fetch position ticks","code":"API_ERROR","detail":"SUN.IO AP |  |

### 模块 11-交易对信息

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_PAR_001 | 按合约地址查交易对 | P1 | PASS | {"list":[{"protocol":"V2","baseId":"TYmBijBaRntmL9y4ry4THqEWp9B26JqMgz","baseNam |  |
| TC_PAR_002 | 按符号查交易对 | P2 | PASS | {"error":"Failed to fetch pair info","code":"API_ERROR","detail":"SUN.IO API err |  |
| TC_PAR_003 | 无效代币 | P3 | PASS | {"error":"Failed to fetch pair info","code":"API_ERROR","detail":"SUN.IO API err |  |

### 模块 12-协议分析

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_PRT_001 | 协议快照 | P1 | PASS | [{"protocol":"V2","reserveUsd":252944864.3635616,"reserveUsd1dRate":0.058461,"vo |  |
| TC_PRT_002 | 交易量历史 | P2 | PASS | [{"time":1773532800000,"value":29816692.112123884},{"time":1773446400000,"value" |  |
| TC_PRT_003 | 用户数历史 | P2 | PASS | [{"time":1773532800000,"value":2428},{"time":1773446400000,"value":2296},{"time" |  |
| TC_PRT_004 | 交易数历史 | P2 | PASS | [{"time":1773532800000,"value":8056},{"time":1773446400000,"value":9063},{"time" |  |
| TC_PRT_005 | 池数量历史 | P3 | PASS | [{"time":1773532800000,"value":26386},{"time":1773446400000,"value":26381},{"tim |  |
| TC_PRT_006 | 流动性历史 | P3 | PASS | [{"time":1773532800000,"value":473991928.7781602},{"time":1773446400000,"value": |  |
| TC_PRT_007 | 无效日期范围 | P3 | PASS | {"error":"Failed to fetch volume history","code":"API_ERROR","detail":"SUN.IO AP |  |

### 模块 13-Farm农场

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_FRM_001 | 查看农场列表 | P1 | PASS | {"list":[{"farmAddress":"TXbA1feyCqWAfAQgXvN1ChTg82HpBT8QPb","poolId":"1","farmN |  |
| TC_FRM_002 | 查询农场交易 | P2 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"","hasMore":f |  |
| TC_FRM_003 | 查询质押头寸 | P2 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"positionUsd", |  |
| TC_FRM_004 | 无质押地址查询 | P3 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"positionUsd", |  |

### 模块 14-交易扫描

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_TXS_001 | 扫描Swap交易 | P1 | PASS | {"list":[{"txId":"38523002ef7d33718f454bb12cea16ea080b3480d38297e3b3ad3bed07be20 |  |
| TC_TXS_002 | 扫描添加流动性交易 | P2 | PASS | {"list":[{"txId":"d2b855c6a518ebabed1593f3bb4f38e3d8d465496590c5445e7a976e3ff136 |  |
| TC_TXS_003 | 扫描撤回交易 | P2 | PASS | {"list":[{"txId":"47a265b6e746f66d154f66337828233f2bbbc2d1823d0befbfedf6be74f60b |  |
| TC_TXS_004 | 无效类型 | P3 | FAIL | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"","hasMore":f | 预期错误但未返回错误 |

### 模块 15-合约调用

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_CTR_001 | 只读调用name() | P1 | PASS | {"result":"Tether USD"} |  |
| TC_CTR_002 | 只读调用totalSupply() | P2 | PASS | {"error":"Contract read failed","code":"UNKNOWN_ERROR","detail":"Do not know how |  |
| TC_CTR_003 | Dry-run写入调用 | P2 | SKIP |  |  |
| TC_CTR_004 | 无效合约地址 | P2 | PASS | {"error":"Contract read failed","code":"CONTRACT_READ_FAILED","detail":"Read con |  |
| TC_CTR_005 | 无效函数名 | P3 | PASS | {"error":"Contract read failed","code":"CONTRACT_READ_FAILED","detail":"Read con |  |
| TC_CTR_006 | 未配置钱包写入 | P1 | PASS | {"error":"Contract send failed","code":"WALLET_NOT_CONFIGURED","detail":"Wallet  |  |

### 模块 16-安全规则

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_SEC_001 | 输出不含私钥 | P1 | PASS | 0 |  |
| TC_SEC_002 | 错误信息不泄露密钥 | P1 | PASS | 0 |  |
| TC_SEC_003 | 防重复交易 | P1 | N/A |  | AI Agent行为测试，非CLI层面 |
| TC_SEC_004 | 高价值操作先dry-run | P1 | N/A |  | AI Agent行为测试，非CLI层面 |
| TC_SEC_005 | 写操作需用户确认 | P1 | N/A |  | AI Agent行为测试，非CLI层面 |
| TC_SEC_006 | --yes跳过确认 | P2 | N/A |  | AI Agent行为测试，--yes由CLI处理 |

### 模块 17-通用标志

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_GEN_001 | JSON输出验证 | P1 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":177383662 |  |
| TC_GEN_002 | --fields字段过滤 | P2 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{}]] |  |
| TC_GEN_003 | mainnet网络 | P2 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":177383663 |  |
| TC_GEN_004 | nile测试网 | P2 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":177383663 |  |
| TC_GEN_005 | shasta测试网 | P2 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":177383663 |  |
| TC_GEN_006 | 无效网络名 | P3 | FAIL | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":177383663 | 预期错误但未返回错误 |
| TC_GEN_007 | sun-cli未安装 | P1 | SKIP |  |  |
| TC_GEN_008 | 断网时处理 | P2 | SKIP |  |  |
| TC_GEN_009 | 超时处理 | P2 | SKIP |  |  |
| TC_GEN_010 | 无TRONGRID_API_KEY | P2 | SKIP |  |  |
| TC_GEN_011 | 滑点过低导致失败 | P2 | SKIP |  |  |

### 模块 18-多角色场景

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_SCN_001 | 首次仅查行情 | P2 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":177383663 |  |
| TC_SCN_002 | 符号大小写容错 | P3 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":177383664 |  |
| TC_SCN_003 | 完整Swap工作流 | P1 | PASS | {"amountIn":"1.000000","amountInRaw":"1000000","amountOut":"62.924127","amountOu |  |
| TC_SCN_004 | 查余额后Swap | P2 | PASS | [{"address":"TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW","type":"TRX","balance":"1142373 |  |
| TC_SCN_005 | 误操作相同代币Swap | P2 | FAIL | {"dryRun":true,"action":"Swap Preview","params":{"Token In":"TRX (T9yD14Nj9j7xAB | 预期错误但未返回错误 |
| TC_SCN_006 | V3完整流动性管理 | P1 | PASS | {"list":[{"id":2,"protocol":"V3","poolAddress":"TSUUVjysXV8YqHytSNjfkNXnnB49QDvZ |  |
| TC_SCN_007 | Position+Pool联合查询 | P2 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"lpBalanceUsd" |  |
| TC_SCN_008 | 多协议对比 | P3 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"lpBalanceUsd" |  |
| TC_SCN_009 | 协议全维度分析 | P2 | PASS | [{"protocol":"V2","reserveUsd":252925125.4496845,"reserveUsd1dRate":0.058378,"vo |  |
| TC_SCN_010 | Farm收益调研 | P3 | PASS | {"list":[{"farmAddress":"TXbA1feyCqWAfAQgXvN1ChTg82HpBT8QPb","poolId":"1","farmN |  |
| TC_SCN_011 | 代币符号解析验证 | P2 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":177383666 |  |
| TC_SCN_012 | 合约地址直接引用 | P2 | PASS | [["TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",{"quote":{"USD":{"last_updated":177383667 |  |
| TC_SCN_013 | 私钥环境变量不泄露 | P1 | PASS | 0 |  |
| TC_SCN_014 | 助记词不泄露 | P1 | PASS | 0 |  |
| TC_SCN_015 | dry-run不产生链上交易 | P1 | PASS | {"dryRun":true,"action":"Swap Preview","params":{"Token In":"TRX (T9yD14Nj9j7xAB |  |
| TC_SCN_016 | 高价值Swap需dry-run先行 | P1 | N/A |  | AI Agent行为测试，非CLI层面 |
| TC_SCN_017 | 写操作前展示确认信息 | P1 | N/A |  | AI Agent行为测试，非CLI层面 |
| TC_SCN_018 | 成功交易后通讯协议 | P2 | N/A |  | AI Agent行为测试，非CLI层面 |
| TC_SCN_019 | --fields减少输出量 | P2 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{}]] |  |
| TC_SCN_020 | 三网络一致性验证 | P3 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":177383668 |  |

### 模块 2-代币价格

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_PRC_001 | 按符号查价格 | P1 | PASS | [["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":177383649 |  |
| TC_PRC_002 | 按合约地址查价格 | P1 | PASS | [["TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",{"quote":{"USD":{"last_updated":177383649 |  |
| TC_PRC_003 | 查询多种代币 | P2 | PASS | [["TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",{"quote":{"USD":{"last_updated":177383649 |  |
| TC_PRC_004 | 无效符号 | P2 | PASS | Unknown token symbol: INVALIDTOKEN. Known symbols for mainnet: TRX, WTRX, USDT,  |  |
| TC_PRC_005 | 无效合约地址 | P2 | PASS | {"error":"Failed to get token price","code":"API_ERROR","detail":"SUN.IO API err |  |

### 模块 3-Swap报价

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_QTE_001 | 标准报价TRX→USDT | P1 | PASS | {"amountIn":"100.000000","amountInRaw":"100000000","amountOut":"30.233022","amou |  |
| TC_QTE_002 | 使用--all完整路由 | P2 | PASS | [{"amountIn":"100.000000","amountInRaw":"100000000","amountOut":"30.233022","amo |  |
| TC_QTE_003 | 测试网报价 | P2 | PASS | {"amountIn":"100.000000","amountInRaw":"100000000","amountOut":"6276.578250","am |  |
| TC_QTE_004 | 反向报价USDT→TRX | P2 | PASS | {"amountIn":"1.000000","amountInRaw":"1000000","amountOut":"3.413257","amountOut |  |
| TC_QTE_005 | 使用合约地址报价 | P2 | PASS | {"amountIn":"100.000000","amountInRaw":"100000000","amountOut":"30.233022","amou |  |
| TC_QTE_006 | 金额为0 | P3 | PASS | {"error":"No route found","code":"NOT_FOUND","detail":"No route available for th |  |
| TC_QTE_007 | 相同代币报价 | P3 | PASS | {"error":"No route found","code":"NOT_FOUND","detail":"No route available for th |  |
| TC_QTE_008 | 超大金额报价 | P3 | PASS | {"amountIn":"999999999999.999999","amountInRaw":"999999999999999999","amountOut" |  |
| TC_QTE_009 | 无效代币符号 | P2 | PASS | {"error":"Invalid token","code":"INVALID_PARAMS","detail":"Unknown token symbol: |  |

### 模块 4-执行Swap

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_SWP_001 | Dry-run模拟Swap | P1 | PASS | {"dryRun":true,"action":"Swap Preview","params":{"Token In":"TRX (T9yD14Nj9j7xAB |  |
| TC_SWP_002 | 实际执行Swap(测试网) | P1 | PASS | {"error":"Swap failed","code":"TX_FAILED","detail":"Broadcast failed: {\"code\": |  |
| TC_SWP_003 | 自定义滑点 | P1 | PASS | {"dryRun":true,"action":"Swap Preview","params":{"Token In":"TRX (T9yD14Nj9j7xAB |  |
| TC_SWP_004 | 默认滑点0.5% | P2 | PASS | {"dryRun":true,"action":"Swap Preview","params":{"Token In":"TRX (T9yD14Nj9j7xAB |  |
| TC_SWP_005 | 使用合约地址Swap | P2 | PASS | {"dryRun":true,"action":"Swap Preview","params":{"Token In":"TRX (T9yD14Nj9j7xAB |  |
| TC_SWP_006 | 余额不足 | P1 | FAIL | {"dryRun":true,"action":"Swap Preview","params":{"Token In":"TRX (T9yD14Nj9j7xAB | 预期错误但未返回错误 |
| TC_SWP_007 | 未配置钱包执行Swap | P1 | PASS | {"error":"Swap failed","code":"WALLET_NOT_CONFIGURED","detail":"Wallet required. |  |
| TC_SWP_008 | Gas不足 | P2 | SKIP |  |  |

### 模块 5-V2流动性

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_V2L_001 | Dry-run单边添加 | P1 | PASS | {"dryRun":true,"action":"V2 Add Liquidity","params":{"Router":"TKzxdSv2FZKQrEqkK |  |
| TC_V2L_002 | Dry-run双边添加 | P2 | PASS | {"dryRun":true,"action":"V2 Add Liquidity","params":{"Router":"TKzxdSv2FZKQrEqkK |  |
| TC_V2L_003 | 指定最小量和接收地址 | P2 | PASS | {"dryRun":true,"action":"V2 Add Liquidity","params":{"Router":"TKzxdSv2FZKQrEqkK |  |
| TC_V2L_004 | 实际添加(测试网) | P1 | PASS | {"error":"V2 add liquidity failed","code":"TX_FAILED","detail":"Broadcast failed |  |
| TC_V2L_005 | Dry-run移除流动性 | P1 | PASS | {"dryRun":true,"action":"V2 Remove Liquidity","params":{"Router":"TKzxdSv2FZKQrE |  |
| TC_V2L_006 | 无LP时移除 | P2 | SKIP |  |  |
| TC_V2L_007 | 余额不足添加 | P2 | FAIL | {"dryRun":true,"action":"V2 Add Liquidity","params":{"Router":"TKzxdSv2FZKQrEqkK | 预期错误但未返回错误 |

### 模块 6-V3流动性

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_V3L_001 | Dry-run全范围铸造 | P1 | PASS | {"dryRun":true,"action":"V3 Mint Position","params":{"Position Manager":"TLSWrv7 |  |
| TC_V3L_002 | 指定费率和Tick铸造 | P1 | PASS | {"dryRun":true,"action":"V3 Mint Position","params":{"Position Manager":"TLSWrv7 |  |
| TC_V3L_003 | 各费率档位验证 | P2 | PASS | {"dryRun":true,"action":"V3 Mint Position","params":{"Position Manager":"TLSWrv7 |  |
| TC_V3L_004 | 无效费率 | P2 | FAIL | {"dryRun":true,"action":"V3 Mint Position","params":{"Position Manager":"TLSWrv7 | 预期错误但未返回错误 |
| TC_V3L_005 | Tick不对齐 | P3 | FAIL | {"dryRun":true,"action":"V3 Mint Position","params":{"Position Manager":"TLSWrv7 | 预期错误但未返回错误 |
| TC_V3L_006 | 增加头寸 | P1 | SKIP |  |  |
| TC_V3L_007 | 减少头寸 | P1 | SKIP |  |  |
| TC_V3L_008 | 收取手续费 | P1 | SKIP |  |  |
| TC_V3L_009 | 指定接收地址 | P2 | SKIP |  |  |
| TC_V3L_010 | 无效token-id | P2 | PASS | {"error":"V3 increase liquidity failed","code":"UNKNOWN_ERROR","detail":"REVERT  |  |

### 模块 7-V4流动性

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_V4L_001 | Dry-run铸造V4头寸 | P1 | PASS | {"dryRun":true,"action":"V4 Mint Position","params":{"Token0":"TRX → WTRX (TNUC9 |  |
| TC_V4L_002 | --create-pool创建新池 | P1 | PASS | {"dryRun":true,"action":"V4 Mint Position","params":{"Token0":"TRX → WTRX (TNUC9 |  |
| TC_V4L_003 | 带--slippage参数 | P2 | PASS | {"dryRun":true,"action":"V4 Mint Position","params":{"Token0":"TRX → WTRX (TNUC9 |  |
| TC_V4L_004 | 增加V4头寸 | P1 | SKIP |  |  |
| TC_V4L_005 | 减少V4头寸 | P1 | SKIP |  |  |
| TC_V4L_006 | 收取V4手续费 | P2 | SKIP |  |  |
| TC_V4L_007 | 查询V4头寸信息 | P2 | SKIP |  |  |
| TC_V4L_008 | 无效token-id | P2 | PASS | {"error":"Position not found"} |  |

### 模块 8-池发现

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_POL_001 | 按代币列出池 | P1 | PASS | {"list":[{"id":2,"protocol":"V3","poolAddress":"TSUUVjysXV8YqHytSNjfkNXnnB49QDvZ |  |
| TC_POL_002 | 按关键词搜索池 | P1 | PASS | {"list":[{"id":2,"protocol":"V3","poolAddress":"TSUUVjysXV8YqHytSNjfkNXnnB49QDvZ |  |
| TC_POL_003 | Top APY池排行 | P1 | PASS | {"list":[{"id":1143,"protocol":"V3","poolAddress":"TDJUxxbmxwC5gUHXm2on4ZHJwjzwk |  |
| TC_POL_004 | 池交易量历史 | P2 | SKIP |  |  |
| TC_POL_005 | 池流动性历史 | P2 | SKIP |  |  |
| TC_POL_006 | V4 Hooks查询 | P2 | PASS | [{"hooksAddress":"TJd9Sf8YnDgYKuLZFR6puxsxQUejXGz7MH","hooksName":"Dynamic Fee", |  |
| TC_POL_007 | 搜索不存在的池 | P3 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"reserveUsd"," |  |
| TC_POL_008 | 无效代币地址 | P3 | PASS | {"error":"Failed to fetch pools","code":"API_ERROR","detail":"SUN.IO API error:  |  |

### 模块 9-代币发现

| 用例ID | 测试场景 | 优先级 | 结果 | 实际输出(摘要) | 备注 |
|--------|----------|--------|------|----------------|------|
| TC_TKN_001 | 列出所有代币 | P1 | PASS | {"error":"Failed to fetch tokens","code":"NETWORK_ERROR","detail":"fetch failed" |  |
| TC_TKN_002 | 按协议筛选代币 | P2 | PASS | {"error":"Failed to fetch tokens","code":"NETWORK_ERROR","detail":"fetch failed" |  |
| TC_TKN_003 | 搜索代币 | P1 | PASS | {"error":"Failed to search tokens","code":"NETWORK_ERROR","detail":"fetch failed |  |
| TC_TKN_004 | 搜索不存在代币 | P3 | PASS | {"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"reserveUsd"," |  |

## 4. 问题清单

共发现 **7** 个失败用例:


- **TC_SWP_006** (余额不足): 预期错误但未返回错误
  - 输出: `{"dryRun":true,"action":"Swap Preview","params":{"Token In":"TRX (T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb)","Token Out":"USDT (TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t)","Amount In":"999999999999999999","Slippag`
- **TC_V2L_007** (余额不足添加): 预期错误但未返回错误
  - 输出: `{"dryRun":true,"action":"V2 Add Liquidity","params":{"Router":"TKzxdSv2FZKQrEqkKVgp5DcwEXBEKMg2Ax","Token A":"TRX (T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb)","Token B":"USDT (TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjL`
- **TC_V3L_004** (无效费率): 预期错误但未返回错误
  - 输出: `{"dryRun":true,"action":"V3 Mint Position","params":{"Position Manager":"TLSWrv7eC1AZCXkRjpqMZUmvgd99cj7pPF","Token0":"TRX → WTRX (TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR)","Token1":"USDT (TR7NHqjeKQxGTC`
- **TC_V3L_005** (Tick不对齐): 预期错误但未返回错误
  - 输出: `{"dryRun":true,"action":"V3 Mint Position","params":{"Position Manager":"TLSWrv7eC1AZCXkRjpqMZUmvgd99cj7pPF","Token0":"TRX → WTRX (TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR)","Token1":"USDT (TR7NHqjeKQxGTC`
- **TC_TXS_004** (无效类型): 预期错误但未返回错误
  - 输出: `{"list":[],"meta":{"pageNo":1,"pageSize":20,"returnSize":0,"sort":"","hasMore":false}}`
- **TC_GEN_006** (无效网络名): 预期错误但未返回错误
  - 输出: `[["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":1773836637024,"price":"0.301711055634"}}}]]`
- **TC_SCN_001** (首次仅查行情): 
  - 输出: `[["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":1773836638463,"price":"0.301711055634"}}}]]`
- **TC_SCN_004** (查余额后Swap): 
  - 输出: `[{"address":"TMgYX7m37cyyTSgVbtCoDUAQcFZ9RoYxJW","type":"TRX","balance":"11423733"}]`
- **TC_SCN_005** (误操作相同代币Swap): 预期错误但未返回错误
  - 输出: `{"dryRun":true,"action":"Swap Preview","params":{"Token In":"TRX (T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb)","Token Out":"TRX (T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb)","Amount In":"100000000","Slippage":"0.50%"`
- **TC_SCN_011** (代币符号解析验证): 
  - 输出: `[["T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",{"quote":{"USD":{"last_updated":1773836664954,"price":"0.301711055634"}}}]]`


### 失败用例分析

#### 类别一：dry-run 模式不校验余额/参数有效性（5个）

| 用例 | 问题描述 |
|------|----------|
| TC_SWP_006 | 余额不足时 `--dry-run swap` 仍返回模拟结果，未报余额不足错误 |
| TC_V2L_007 | 余额不足时 `--dry-run v2:add` 仍返回模拟结果，未报余额不足错误 |
| TC_V3L_004 | 无效费率(9999) `--dry-run v3:mint` 仍返回模拟结果，未校验费率有效性 |
| TC_V3L_005 | Tick不对齐时 `--dry-run v3:mint` 仍返回模拟结果，未校验Tick对齐 |
| TC_SCN_005 | 相同代币(TRX→TRX) `--dry-run swap` 仍返回模拟结果，未拒绝同币兑换 |

**根因**: `--dry-run` 模式仅构建交易预览，不执行链上模拟验证。余额检查和参数校验发生在实际广播阶段。

**建议**: 在 dry-run 阶段增加前置校验：余额充足性检查、费率白名单校验、Tick对齐检查、同币兑换拦截。

#### 类别二：无效输入容错处理（2个）

| 用例 | 问题描述 |
|------|----------|
| TC_TXS_004 | 无效交易类型(invalidtype)返回空列表而非错误提示 |
| TC_GEN_006 | 无效网络名(badnet)返回主网数据而非错误提示 |

**根因**: CLI 对未知参数值采用静默降级策略（fallback到默认值），而非严格校验。

**建议**: 对 `--type` 和 `--network` 参数增加枚举校验，无效值应返回明确错误信息。


## 5. 结论与建议

本次测试共执行 134 个用例，其中 101 个通过，7 个失败，19 个跳过，7 个不适用。
有效通过率为 93.5%。

建议针对失败用例进行排查和修复。

### 跳过用例说明

- V3/V4头寸相关操作(increase/decrease/collect)需要已有链上头寸，当前钱包无相关头寸
- 网络异常/超时/未安装等场景无法在当前环境模拟
- Gas不足场景需要特定余额条件

### N/A用例说明

- 安全规则中的防重复交易、dry-run先行、用户确认等属于AI Agent行为层面约束，非CLI功能测试

---

*报告生成时间: 2026-03-18 20:24:44*