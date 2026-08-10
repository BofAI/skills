# Twitter Digest 精简分诊、Passcode 与限流实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 发布一个不生成回复内容、首次配置更友好、默认只检查近期 X Chat 且能够避免空页和重复 429 的 twitter-digest 版本。

**Architecture:** 保留现有 API-only wrapper 和 Chat XDK 解密架构。用显式扫描 profile 控制默认/扩展模式，用独立 owner-only 状态模块保存脱敏 429 冷却，并让 digest context 只输出事实、状态和覆盖缺口。

**Tech Stack:** Python 3.10+、标准库 `unittest`/`unittest.mock`、`chatxdk==0.4.3`、POSIX shell installer。

## Global Constraints

- 永久不生成、推荐、改写或发送任何回复内容。
- OAuth scope 保持 `tweet.read users.read offline.access dm.read`，不增加 write scope。
- 默认 X Chat：24 小时、最多 10 个会话、每个 1 页、最多 10 次事件请求。
- 主动扩展：最多 50 个会话、每个 3 页、最多 20 次事件请求。
- 确认一个会话最新可读消息早于当前窗口后立即停止。
- 空页最多连续 3 页，会话列表整轮最多 5 次请求，重复游标立即停止。
- passcode 最多本地输入 3 次，不保存，不因重试重新读取公钥。
- 429 冷却状态不得包含 API 路径、ID、Token、正文、密文或响应体。
- 最终安装入口必须是 `curl ... | env ... sh`。
- 不修改现有未提交的 `twitter-mcp` 文件。

---

### Task 1: 删除回复内容并精简上下文契约

**Files:**
- Modify: `twitter-digest/SKILL.md`
- Modify: `twitter-digest/scripts/digest_context.py`
- Test: `twitter-digest/tests/test_digest_context_chat.py`
- Test: `twitter-digest/tests/test_security_contract.py`

**Interfaces:**
- Consumes: `build_digest_facts()` 与 `render_context_slice()` 当前运行事实。
- Produces: 无回复草稿指令的固定六段输出契约，以及 `X Chat 已按 X 返回顺序检查 N 个会话。`。

- [ ] **Step 1: 写失败测试**

要求 Skill 不再包含 `建议回复草稿`，明确包含 `不得生成、推荐或改写任何回复内容`；DM context 必须包含新覆盖文案而不包含“最近的 N 个会话”。

- [ ] **Step 2: 运行 RED**

```bash
python3 -m unittest twitter-digest/tests/test_digest_context_chat.py twitter-digest/tests/test_security_contract.py -v
```

预期：旧 Skill 和旧 context 文案使测试失败。

- [ ] **Step 3: 最小实现**

固定输出为“今日必须知道、今日必须处理、Mentions、Timeline、私信、数据缺口”；删除草稿段和提供替代草稿的规则；修改 context summary rules 和不完整扫描文案。

- [ ] **Step 4: 运行 GREEN 并提交**

```bash
python3 -m unittest twitter-digest/tests/test_digest_context_chat.py twitter-digest/tests/test_security_contract.py -v
git add twitter-digest/SKILL.md twitter-digest/scripts/digest_context.py twitter-digest/tests/test_digest_context_chat.py twitter-digest/tests/test_security_contract.py
git commit -m "fix(twitter-digest): remove reply content"
```

### Task 2: Passcode 状态引导与本地重试

**Files:**
- Modify: `twitter-digest/scripts/configure_chat.py`
- Modify: `twitter-digest/scripts/configure_all.py`
- Modify: `twitter-digest/scripts/run_daily_digest.py`
- Test: `twitter-digest/tests/test_configure_chat.py`
- Test: `twitter-digest/tests/test_security_contract.py`

**Interfaces:**
- Produces: `choose_missing_passcode_action(input_fn=input, open_url=webbrowser.open) -> None`。
- Produces: `unlock_with_passcode_retries(python, record, attempts=3) -> bytes | None`。
- `configure()` 只调用一次 `api_get()` 和一次 `ensure_runtime()`，随后最多执行三次本地 unlock。

- [ ] **Step 1: 写失败测试**

测试无 passcode-backed key 时显示中文并且不准备 runtime；测试三次输入只调用一次公钥读取和一次 runtime，前两次失败、第三次成功才保存配置；测试 Enter 才打开 X 消息页、q 不打开。

- [ ] **Step 2: 运行 RED**

```bash
python3 -m unittest twitter-digest/tests/test_configure_chat.py twitter-digest/tests/test_security_contract.py -v
```

- [ ] **Step 3: 实现状态流程**

无可用 key 时打印中文说明；交互 Terminal 允许 Enter 打开 `https://x.com/messages` 或 q 退出。runtime 准备后进入最多 3 次 getpass 循环；失败只显示中文说明；成功后才保存配置。统一三个入口的 Terminal description。

- [ ] **Step 4: 运行 GREEN 并提交**

```bash
python3 -m unittest twitter-digest/tests/test_configure_chat.py twitter-digest/tests/test_security_contract.py -v
git add twitter-digest/scripts/configure_chat.py twitter-digest/scripts/configure_all.py twitter-digest/scripts/run_daily_digest.py twitter-digest/tests/test_configure_chat.py twitter-digest/tests/test_security_contract.py
git commit -m "fix(twitter-digest): guide X Chat passcode setup"
```

### Task 3: 默认近期模式与主动扩展模式

**Files:**
- Modify: `twitter-digest/scripts/run_daily_digest.py`
- Modify: `twitter-digest/scripts/chat_x_digest.py`
- Modify: `twitter-digest/SKILL.md`
- Test: `twitter-digest/tests/test_chat_x_digest.py`
- Test: `twitter-digest/tests/test_security_contract.py`

**Interfaces:**
- Wrapper option: `--chat-scan {recent,more}`，默认 `recent`。
- Collector arguments: `--max-conversations`、`--max-event-requests`、`--max-event-pages`。
- 168 小时窗口自动选择 `more`，显式 `--chat-scan more` 也选择扩展 profile。

- [ ] **Step 1: 写失败测试**

断言 recent profile 等于 `{"max_conversations": 10, "event_requests": 10, "event_pages": 1}`；more profile 等于 `{"max_conversations": 50, "event_requests": 20, "event_pages": 3}`。wrapper command 测试断言普通运行和扩展运行传入相应参数。

- [ ] **Step 2: 运行 RED**

```bash
python3 -m unittest twitter-digest/tests/test_chat_x_digest.py twitter-digest/tests/test_security_contract.py -v
```

- [ ] **Step 3: 实现 profile**

collector 不再依赖硬编码 50/20/3。wrapper 根据 `chat_scan` 与窗口组装参数。Skill 将“查看更多私信”映射为 `--chat-scan more`，将“最近七天 Chat”映射为 `--chat-window-hours 168 --chat-scan more`。

- [ ] **Step 4: 运行 GREEN 并提交**

```bash
python3 -m unittest twitter-digest/tests/test_chat_x_digest.py twitter-digest/tests/test_security_contract.py -v
git add twitter-digest/scripts/run_daily_digest.py twitter-digest/scripts/chat_x_digest.py twitter-digest/SKILL.md twitter-digest/tests/test_chat_x_digest.py twitter-digest/tests/test_security_contract.py
git commit -m "feat(twitter-digest): add bounded X Chat scan profiles"
```

### Task 4: 第一个确认旧会话立即停止

**Files:**
- Modify: `twitter-digest/scripts/chat_x_digest.py`
- Test: `twitter-digest/tests/test_chat_x_digest.py`

**Interfaces:**
- Produces: `conversation_is_before_window(decrypted_rows, raw_events, cutoff) -> bool`，只有可靠的最新可读消息时间存在且早于 cutoff 时返回 true。

- [ ] **Step 1: 写失败测试**

覆盖可靠旧消息返回 true、缺少时间返回 false；端到端 fixture 返回 old/new 两个会话，断言 new 的 events API 不调用，stop reason 为 `first_conversation_before_window` 且 complete=false。

- [ ] **Step 2: RED → 最小实现 → GREEN → 提交**

```bash
python3 -m unittest twitter-digest/tests/test_chat_x_digest.py -v
git add twitter-digest/scripts/chat_x_digest.py twitter-digest/tests/test_chat_x_digest.py
git commit -m "fix(twitter-digest): stop after first confirmed old chat"
```

### Task 5: 空页、重复游标和列表请求预算

**Files:**
- Modify: `twitter-digest/scripts/chat_x_digest.py`
- Test: `twitter-digest/tests/test_chat_x_digest.py`

**Interfaces:**
- Extend `collect_conversations(token, maximum, max_requests=5, max_empty_pages=3)` metadata with `pages_used`、`empty_pages`、`stop_reason`。

- [ ] **Step 1: 写失败测试**

用字面 fixture 覆盖：空页后有数据、连续 3 空页、重复 token、`has_more=true` 无 token。断言调用次数分别为 2、3、2、1；后三者 complete=false，stop reason 分别为 `empty_page_limit`、`repeated_pagination_token`、`missing_pagination_token`。

- [ ] **Step 2: 运行 RED**

```bash
python3 -m unittest twitter-digest/tests/test_chat_x_digest.py -v
```

- [ ] **Step 3: 最小实现**

维护 `seen_tokens`、`pages_used` 和连续空页计数。只有非空页将连续空页清零。达到边界时保留已收集会话并标记 partial；空页不进入主事件循环。

- [ ] **Step 4: GREEN 并提交**

```bash
python3 -m unittest twitter-digest/tests/test_chat_x_digest.py -v
git add twitter-digest/scripts/chat_x_digest.py twitter-digest/tests/test_chat_x_digest.py
git commit -m "fix(twitter-digest): bound empty X Chat pages"
```

### Task 6: 跨运行 429 冷却

**Files:**
- Create: `twitter-digest/scripts/chat_rate_limit_store.py`
- Create: `twitter-digest/tests/test_chat_rate_limit_store.py`
- Modify: `twitter-digest/scripts/chat_config_store.py`
- Modify: `twitter-digest/scripts/chat_x_digest.py`
- Modify: `twitter-digest/scripts/configure_chat.py`
- Test: `twitter-digest/tests/test_chat_x_digest.py`
- Test: `twitter-digest/tests/test_configure_chat.py`

**Interfaces:**
- `record_rate_limit(endpoint: str, retry_after_seconds: int | None, now: float | None = None) -> None`
- `active_rate_limit(endpoint: str, now: float | None = None) -> int | None`
- `clear_rate_limits() -> None`
- State path: `.state/chat/rate_limits.json`，mode 0600 under 0700 directory。

- [ ] **Step 1: 写 store 的失败测试**

记录 events 冷却 90 秒，now=1030 应返回剩余 60 秒，now=1091 应返回 None 并清理；未知 reset 不写文件；非法 endpoint 不写；JSON 只包含 endpoint/retry_after_epoch 且权限正确。

- [ ] **Step 2: 运行 RED**

```bash
python3 -m unittest twitter-digest/tests/test_chat_rate_limit_store.py -v
```

- [ ] **Step 3: 实现 owner-only store**

使用临时文件、`os.replace` 和 `ensure_private_dir`。过期记录读取时删除。`clear_chat_config()` 同时清理冷却文件。

- [ ] **Step 4: 写接入失败测试**

先记录冷却再调用 `api_get`，断言抛出结构化 429 且 `urlopen.assert_not_called()`。模拟真实 HTTP 429 后断言 store 被调用一次。配置公钥请求采用相同逻辑。

- [ ] **Step 5: 接入、运行 GREEN 并提交**

```bash
python3 -m unittest twitter-digest/tests/test_chat_rate_limit_store.py twitter-digest/tests/test_chat_x_digest.py twitter-digest/tests/test_configure_chat.py -v
git add twitter-digest/scripts/chat_rate_limit_store.py twitter-digest/scripts/chat_config_store.py twitter-digest/scripts/chat_x_digest.py twitter-digest/scripts/configure_chat.py twitter-digest/tests/test_chat_rate_limit_store.py twitter-digest/tests/test_chat_x_digest.py twitter-digest/tests/test_configure_chat.py
git commit -m "fix(twitter-digest): persist safe X Chat cooldowns"
```

### Task 7: 发布 beta.13 与完整验证

**Files:**
- Modify: `twitter-digest/install.sh`
- Modify: `twitter-digest/README.md`
- Modify: `twitter-digest/RUNBOOK.md`
- Modify: `twitter-digest/tests/test_security_contract.py`

**Interfaces:**
- Produces tag contract `v1.5.14-beta.13` and Codex/Claude curl commands。

- [ ] **Step 1: 先把版本测试改为 beta.13 并确认 RED**

```bash
python3 -m unittest twitter-digest/tests/test_security_contract.py -v
```

- [ ] **Step 2: 更新 README、RUNBOOK 和 installer 默认标签**

文档只展示 curl 安装；说明默认近期模式、`--chat-scan more`、七天模式和 passcode 指引。

- [ ] **Step 3: 完整验证**

```bash
python3 -m unittest discover -s twitter-digest/tests -p 'test_*.py' -v
python3 twitter-digest/scripts/install.py --help
sh -n twitter-digest/install.sh twitter-digest/uninstall.sh
git diff --check
```

- [ ] **Step 4: 提交发布准备**

```bash
git add twitter-digest/install.sh twitter-digest/README.md twitter-digest/RUNBOOK.md twitter-digest/tests/test_security_contract.py
git commit -m "release(twitter-digest): prepare v1.5.14-beta.13"
```

- [ ] **Step 5: 用户确认发布后推送**

创建 annotated tag `v1.5.14-beta.13`，推送 `twitter-digest-api-only` 与标签。从 raw GitHub URL 下载 installer，运行 `sh -n` 并确认默认标签后才能提供最终 curl 命令。

