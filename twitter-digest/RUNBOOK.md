# X/Twitter Digest Skill Runbook

## 目标

`twitter-digest` 读取用户自己的 X/Twitter 数据并生成中文日报。抓数据层支持 API 和本地已登录浏览器两种来源。

默认入口是 `scripts/run_daily_digest.py`，默认 `--source auto`。普通日报始终优先走 API；如果没有 API 配置、token 刷新失败或认证失效，脚本会先触发 API 配置，配置成功后继续 API 采集。只有用户主动要求浏览器，或命令显式传入 `--source browser` 时，才强制浏览器。API 模式只抓公开数据，不打开浏览器。

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
  - 已配置 API 时走 API。
  - 没有 API 配置时走浏览器。
  - 已配置 API 但 token 刷新失败或认证失效时触发 API 重配置。
  - 重配置成功后继续 API 采集。
  - 用户主动要求浏览器或显式 `--source browser` 时强制浏览器。
  - API source 已选择时不回退浏览器；认证类错误只重配一次，其他 API 失败就报错或写 data gap。
  - 使用 API 且保存了 refresh token 时自动刷新过期 access token。
```

强制浏览器：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --source browser
```

强制 API：

```bash
X_BEARER_TOKEN=... python3 twitter-digest/scripts/run_daily_digest.py --source api --handle <handle>
```

API 模式重点用于更稳定地抓公开数据。API 模式不会打开浏览器。X Chat / DM 内容只在显式浏览器模式中读取；API 模式不使用 DM 作为日报判断依据。

来源隔离规则：

- API 模式只运行 `api_x_digest.py`，不启动浏览器、不读取浏览器 profile、不用浏览器补采 API 缺口。
- 浏览器模式只运行 `browser_x_digest.py`，不读取 API token、不合并 API collector 输出。
- 默认 `--source auto` 每次只选择一个来源，不合并 API 和浏览器两边的数据。
- API 模式输出的 DM 浏览器确认提示只是 data gap，不代表浏览器数据已被采集。

## 对话内 API 授权

用户不需要自己 export 环境变量。用户在对话里说“配置 X API”时，Agent 运行：

```bash
python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api
```

如果当前对话环境没有可交互 TTY，脚本会自动打开一个真实 Terminal 窗口来输入 Client ID / Secret 和等待 OAuth callback。不要把 `configure_api.py --oauth` 放到后台 shell 里跑；如果误从临时 clone 目录运行，脚本也会自动切回已安装的 skill 目录，避免把配置写到 `/tmp`。

推荐路径是 OAuth2 PKCE，适合用户自己申请的本地 X Developer App：

1. 脚本直接进入 OAuth2 配置。
2. 脚本提示输入 X App 的 Client ID。
3. 脚本提示输入 X App 的 Client Secret；public PKCE app 可留空。
4. 脚本打开 X 授权页。
5. 用户在浏览器里授权 app。
6. 脚本通过本地 callback 收到授权码。
7. 脚本换取 user access token 和 refresh token。
8. token 保存到已安装 skill 的 `.state/api_config.json`，文件权限尽量设为 owner-only。
9. 后续普通日报自动走 API；要临时使用浏览器时显式运行 `--source browser`。

用户只需要准备：

```text
CLIENT_ID
CLIENT_SECRET（如 App 要求）
```

`ACCESS_TOKEN` 和 `REFRESH_TOKEN` 由授权流程生成。

配置成功后，后续日报不再要求用户输入 Client ID、Secret 或重新授权。普通 `run_daily_digest.py` 会读取 `.state/api_config.json` 并默认走 API；如果没有这个 API 配置文件，普通日报会走浏览器：

- OAuth2：如果保存了 refresh token，access token 快过期时自动 refresh。
- 如果 token 被撤销、过期且无法刷新，或 API 返回 401 等认证错误，普通日报命令会重新打开配置并重试一次。
- 如果权限变更、tier 不支持、限流或 endpoint 不可用，脚本把 endpoint 错误写入 data gap 或失败，不自动切到浏览器。

OAuth1 PIN 不再作为正常配置路径：验证中它不能可靠读取 DM，不适合这个日报 skill 的核心目标。

X Developer App 里需要配置 callback URL，默认：

```text
http://127.0.0.1:8765/callback
```

如果用户已有 user-context access token，可以单独运行 `python3 ~/.claude/skills/twitter-digest/scripts/run_daily_digest.py --configure-api-token`。不要要求用户手动配置 shell 环境变量；这是调试路径，不是主流程。

## 安装与依赖检查

安装命令：

```bash
python3 twitter-digest/scripts/install.py
```

安装脚本默认安装到当前工具对应的 skills 目录：

- 在 Codex 里运行：`~/.codex/skills/twitter-digest`
- 在 Claude Code 里运行：`~/.claude/skills/twitter-digest`

如需显式指定：

```bash
python3 twitter-digest/scripts/install.py --client codex
python3 twitter-digest/scripts/install.py --client claude
```

安装脚本会检查：

- Python 3.9+
- Google Chrome、Chromium、Microsoft Edge 或 Brave

如果缺少支持的 Chromium 浏览器，安装脚本会停止并提示先安装浏览器。浏览器用于未配置 API 时的默认本地 X 页面采集、显式 `--source browser` 采集，以及 OAuth 授权页打开。已配置 API 的默认日报不会启动浏览器采集。

如果浏览器会稍后安装，可以显式跳过检查：

```bash
python3 twitter-digest/scripts/install.py --skip-browser-check
```

安装脚本不会复制 `.state/`，因此不会把开发机器上的 X 登录态、运行结果或 DM 原文复制到用户的 skill 安装目录。

## 显式浏览器模式与登录状态

以下流程只适用于用户主动要求浏览器采集，或命令显式传入 `--source browser`。

首次运行：

1. 脚本启动专用浏览器 profile。
2. 如果没有 X 登录态，打开可见浏览器窗口。
3. 用户在窗口里正常登录 X。
4. 登录态保存在 `twitter-digest/.state/chrome-profile`。

后续浏览器运行：

1. 默认 headless 启动浏览器。
2. 复用 `twitter-digest/.state/chrome-profile`。
3. 如果登录态有效，不弹浏览器。
4. 如果登录失效，再打开可见浏览器让用户重新登录。

浏览器日报必须识别当前登录账号的 handle。脚本会先从 X 的账号切换器、Profile 导航和账号相关 DOM 自动识别；如果 headless 识别不到，会打开可见浏览器重试。仍识别不到时直接停止，不生成日报。此时让用户确认可见浏览器里登录的是正确账号，或显式运行：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --handle <handle>
```

不会读取用户常用浏览器 profile，也不会要求用户复制 cookie/token。

## 默认采集范围

API 默认页面：

- `home`：首页时间线，用于看热点。
- `own_profile`：自己的主页，用于看自己最近发帖/互动。
- `mentions` / `mentions_search`：谁 @ 了当前账号。

显式浏览器模式页面：

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
--min-public-scrolls 5
--max-public-items 100
--public-window-hours 24
```

流程：

1. 打开公开页面。
2. 读取已加载的 `article`。
3. 滚动页面并继续读取。
4. 去重。
5. 最多保留 100 条浏览器公开帖子。API public 默认最多保留 300 条。
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

DM 只在显式浏览器模式中读取。API 模式不采集 DM，也不根据 API DM 结果判断“没有私信”。

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
--dm-list-scrolls 20
--dm-max-messages 2000
--dm-window-hours 0
```

含义：

- 最多向上滚动 200 次。
- 最多保留 2000 条消息气泡。
- `--dm-list-scrolls 20` 表示先向下扫描左侧会话列表，尽量覆盖今天会话。
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

如果需要检查本次采集计数、DM 状态或数据缺口，不要临时写 `python3 -c` 或 shell 片段遍历 JSON。使用固定检查脚本：

```bash
python3 twitter-digest/scripts/inspect_digest.py
```

该脚本只输出计数、加载状态和数据缺口，不输出 DM 正文。

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
- 跳过 DM 生成日报。

## 常用命令

完整日报：

```bash
python3 twitter-digest/scripts/run_daily_digest.py
```

跳过 DM：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --source browser --no-dms
```

强制显示浏览器：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --source browser --headed
```

清理登录态并重新登录：

```bash
rm -rf twitter-digest/.state/chrome-profile
```
