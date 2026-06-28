# X/Twitter Digest Skill Runbook

## 目标

`twitter-digest` 读取用户自己的 X/Twitter 数据并生成中文日报。抓数据层支持 API 和本地已登录浏览器两种来源。

默认入口是 `scripts/run_daily_digest.py`。如果已经通过对话内 OAuth 授权保存了 user-context token，或环境里配置了 X API token，它优先用 API 抓公开数据；如果没有 API 配置，它自动回退到浏览器抓取。读取 X Chat / DM 内容时仍使用本地浏览器，因为普通 API 配置通常没有私信读取能力。

核心链路：

```text
run_daily_digest.py
-> 选择 API 或浏览器 collector
-> 生成 digest-input.*
-> 归一化生成 digest-context.md
-> Agent 只基于 digest-context.md 写中文日报
```

## 抓数据脚本分层

当前有三层脚本：

```text
scripts/browser_x_digest.py
  通过本地浏览器抓取数据。

scripts/api_x_digest.py
  通过 X API 抓取数据。

scripts/run_daily_digest.py
  上层入口。默认 --source auto：
  - 检测到已保存 OAuth token 或 X_BEARER_TOKEN / TWITTER_BEARER_TOKEN 时走 API。
  - 没有 API 配置时走浏览器。
  - 保存了 refresh token 时自动刷新过期 access token。
```

强制浏览器：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --source browser
```

强制 API：

```bash
X_BEARER_TOKEN=... python3 twitter-digest/scripts/run_daily_digest.py --source api --handle <handle>
```

API 模式重点用于更稳定地抓公开数据。X Chat / DM 内容仍以浏览器模式为准；如果 API 模式无法读取 DM，会在 `digest-context` 的 Data Gaps 中标注。

## 对话内 API 授权

用户不需要自己 export 环境变量。用户在对话里说“配置 X API”时，Agent 运行：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --configure-api
```

推荐路径是 OAuth2 PKCE，适合用户自己申请的本地 X Developer App：

1. 脚本弹出 OAuth / Paste Token 选择。
2. 用户选择 OAuth2。
3. 脚本提示输入 X App 的 Client ID。
4. 脚本提示输入 X App 的 Client Secret；public PKCE app 可留空。
5. 脚本打开 X 授权页。
6. 用户在浏览器里授权 app。
7. 脚本通过本地 callback 收到授权码。
8. 脚本换取 user access token 和 refresh token。
9. token 保存到 `twitter-digest/.state/api_config.json`，文件权限尽量设为 owner-only。
10. 后续日报 `--source auto` 自动走 API。

用户只需要准备：

```text
CLIENT_ID
CLIENT_SECRET（如 App 要求）
```

`ACCESS_TOKEN` 和 `REFRESH_TOKEN` 由授权流程生成。

配置成功后，后续日报不再要求用户输入 Client ID、Secret 或重新授权。`run_daily_digest.py` 会读取 `.state/api_config.json`：

- OAuth2：如果保存了 refresh token，access token 快过期时自动 refresh。
- 如果 token 被撤销、权限变更、tier 不支持或 API 返回 401/403/429，脚本把 endpoint 错误写入 data gap，Agent 再提示用户是否重新配置。

OAuth1 PIN 不再作为正常配置路径：验证中它不能可靠读取 DM，不适合这个日报 skill 的核心目标。

X Developer App 里需要配置 callback URL，默认：

```text
http://127.0.0.1:8765/callback
```

如果用户已有 user-context access token，也可以在配置向导里选择 Paste Token。不要要求用户手动配置 shell 环境变量；这是调试路径，不是主流程。

## 安装与依赖检查

安装命令：

```bash
python3 twitter-digest/scripts/install.py
```

安装脚本会检查：

- Python 3.10+
- Google Chrome、Chromium、Microsoft Edge 或 Brave

如果缺少支持的 Chromium 浏览器，安装脚本会停止并提示先安装浏览器。浏览器必须存在，因为后续采集完全依赖本地浏览器打开 `x.com`。

如果浏览器会稍后安装，可以显式跳过检查：

```bash
python3 twitter-digest/scripts/install.py --skip-browser-check
```

安装脚本不会复制 `.state/`，因此不会把开发机器上的 X 登录态、运行结果或 DM 原文复制到用户的 skill 安装目录。

## 登录与浏览器状态

首次运行：

1. 脚本启动专用浏览器 profile。
2. 如果没有 X 登录态，打开可见浏览器窗口。
3. 用户在窗口里正常登录 X。
4. 登录态保存在 `twitter-digest/.state/chrome-profile`。

后续运行：

1. 默认 headless 启动浏览器。
2. 复用 `twitter-digest/.state/chrome-profile`。
3. 如果登录态有效，不弹浏览器。
4. 如果登录失效，再打开可见浏览器让用户重新登录。

不会读取用户常用浏览器 profile，也不会要求用户复制 cookie/token。

## 默认采集范围

默认页面：

- `home`：首页时间线，用于看热点。
- `own_profile`：自己的主页，用于看自己最近发帖/互动。
- `mentions_search`：搜索 `@当前账号`。
- `mentions_notifications`：通知里的 @ 提及。
- `messages`：X Chat / DM。

默认不采集关键词。只有显式传 `--keywords` 时才增加关键词搜索页。

## 公开页采集逻辑

公开页包括：

- `home`
- `own_profile`
- `mentions_search`
- `mentions_notifications`

默认参数：

```text
--scrolls 40
--max-public-items 300
--public-window-hours 24
```

流程：

1. 打开公开页面。
2. 读取已加载的 `article`。
3. 滚动页面并继续读取。
4. 去重。
5. 最多保留 300 条公开帖子。
6. 如果已加载帖子的时间戳显示超过 24 小时窗口，提前停止。

每条公开帖子会尽量提取：

- 帖子文本
- 时间
- tweet URL
- 作者 URL
- 图片 / 视频缩略图 URL
- 外部链接
- 卡片 / 引用链接

公开帖子数量表示“本次浏览器加载到的帖子”，不是完整 X 历史。

## DM 采集逻辑

DM 默认读取。

先读取 X Chat 左侧会话列表，并统计今天可见会话：

```text
today visible = last_from_me + waiting_reply
```

定义：

- `last_from_me`：列表最后预览是 `You:` / `You sent` / `你:`，表示最后一条是用户发出的。
- `waiting_reply`：列表最后预览不是用户发出的，表示最后一条来自对方，等待用户处理。

规则：

- `last_from_me` 只计数，不打开正文。
- `waiting_reply` 会打开正文。
- 只有 `waiting_reply` 会进入 DM 摘要判断。

## DM 会话完整性

对每个 `waiting_reply` 会话，脚本会尽量完整加载浏览器可读取的会话历史。

默认参数：

```text
--dm-scrolls 200
--dm-max-messages 2000
--dm-window-hours 0
```

含义：

- 最多向上滚动 200 次。
- 最多保留 2000 条消息气泡。
- `--dm-window-hours 0` 表示不按 24 小时截断 DM 历史。
- 会尽量滚到对话顶部。
- 如果没有滚到顶部或命中消息上限，会在 `digest-context` 里记录 `dm_thread_incomplete`。

DM 每条消息会尽量提取：

- 发送方向：`me` / `other`
- 时间
- 文本
- 链接
- 图片 / 视频 / 卡片 metadata

## Passcode 与加密私信

如果 X Chat 要求 passcode 或加密恢复：

1. headless 采集会检测到 passcode 页面。
2. 脚本自动打开可见浏览器窗口。
3. 用户自己输入或完成 passcode 设置。
4. 脚本等待 Messages 页面真正可读。
5. 继续采集 DM。
6. 完成后可回到 headless。

脚本不会帮用户设置、输入或保存 passcode。

## 输出文件

每次运行输出在：

```text
twitter-digest/.state/run/
```

主要文件：

```text
digest-input.json
digest-input.md
digest-context.json
digest-context.md
```

用途：

- `digest-input.*`：浏览器原始采集结果，只用于 debug。
- `digest-context.*`：给 Agent 写日报的正式输入。

正常总结只读：

```text
twitter-digest/.state/run/digest-context.md
```

不生成长期 `memory.json`，不生成 `daily/` 历史归档。

## digest-context 内容

`digest-context.md` 包括：

- Run 信息：日期、生成时间、时区、当前账号。
- DM Facts：DM 状态、今日可见会话数、最后我发出数量、等我回复数量、捕获消息数量。
- DM Thread Context：只包含需要回复的会话，带原始 label、URL、加载状态和消息上下文。
- Public Counts：每个公开页抓到多少帖子。
- Public Items：公开帖子文本、URL、媒体、外链、卡片。
- Data Gaps：任何没读到或没读完整的数据缺口。

## 日报生成规则

Agent 只基于 `digest-context.md` 生成中文日报。

默认结构：

```markdown
## X 日报 - YYYY-MM-DD

**今日总结**

**该处理**

**谁 @ 了你**

**私信（DM）**

**时间线热点**

**你的动态**

**建议回复草稿**

**数据缺口**
```

总结原则：

- 先判断今天有没有需要处理的风险、机会或回复。
- @ 提及按重要性分组。
- DM 只重点总结 `waiting_reply`。
- `last_from_me` 不当作待处理。
- 垃圾、钓鱼、低质营销只计数，不展开。
- 私信内容只做必要摘要，不贴完整隐私历史。
- 图片/链接信息只作为理解上下文，不能凭空描述图片内容。
- 不自动发帖、不自动回复、不点赞、不关注。

## 用户可以获得的信息

用户可以问：

- 生成今日 X 日报。
- 今天谁 @ 我了？
- 哪些 DM 等我回复？
- 有没有重要私信？
- 哪些私信是垃圾/钓鱼？
- 今天时间线有什么热点？
- 我的账号今天有没有互动？
- 帮我起草回复，但不要发送。
- 这次哪些数据没读到？
- 给我看 `digest-context`。
- 只测试 DM 扫描。
- 跳过 DM 生成日报。

## 常用命令

完整日报：

```bash
python3 twitter-digest/scripts/run_daily_digest.py
```

跳过 DM：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --no-dms
```

强制显示浏览器：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --headed
```

DM 专用测试：

```bash
python3 twitter-digest/scripts/test_dm_collection.py
```

快速 DM 测试：

```bash
python3 twitter-digest/scripts/test_dm_collection.py \
  --dm-threads 1 \
  --dm-scrolls 20 \
  --dm-max-messages 200
```

清理登录态并重新登录：

```bash
rm -rf twitter-digest/.state/chrome-profile
```
