# X/Twitter Digest 功能 / 规则 / 流程说明

## 1. 功能

`twitter-digest` 用本地浏览器读取用户自己的 X/Twitter 页面，并生成中文日报。

默认采集内容：

- Home timeline：时间线热点
- Mentions search：搜索谁 @ 了当前账号
- Mentions notifications：通知里的 @
- Own profile：当前账号主页动态
- DMs：私信页面可见会话

默认不采集关键词。只有显式传 `--keywords` 时才做关键词搜索。

公开页采集范围：

- timeline、profile、mentions 默认按日报目标加载近 24 小时内容。
- 每个公开页默认最多滚动 40 次，并最多保留 300 条公开帖子进入 `digest-context`。
- 如果已加载帖子的时间戳显示已经超过 24 小时窗口，会提前停止滚动。
- 公开帖子数量表示“本次浏览器加载到的帖子”，不是完整 X 历史。

## 2. 数据保存位置

安装脚本会把旧的 `twitter-briefing`、`twitter-briefing.bak` 或已有 `twitter-digest` 安装迁移到 `~/.claude/skills/.backups/`，并把备份里的 `SKILL.md` 改成 `SKILL.md.disabled`，避免 Claude Code 加载重复旧 skill。

登录状态保存在：

```text
twitter-digest/.state/chrome-profile
```

这不是 `/tmp`。只要这个目录不删除、X 登录态不过期，后续运行会复用。

每次运行的临时采集结果保存在：

```text
twitter-digest/.state/run/
```

主要文件：

```text
twitter-digest/.state/run/digest-input.json
twitter-digest/.state/run/digest-input.md
twitter-digest/.state/run/digest-context.json
twitter-digest/.state/run/digest-context.md
```

用途：

- `digest-context.md/json`：最终总结主输入，包含本次采集归一化后的 `Final Summary Facts`。
- `digest-input.md/json`：原始浏览器采集结果，只在需要核对细节或排查抓取问题时使用。

不生成长期 `memory.json`，不生成 `daily/` 历史归档。
`twitter-digest/.state/run/` 会尽量设置为 700 权限，避免把当次 DM 原文放到全局可读的 `/tmp`。

## 3. 运行规则

- 只使用本地浏览器抓取。
- 不使用 X 开发者 API。
- 不使用 MCP。
- 不要求用户复制 cookie 或 token。
- 默认 headless 运行。
- 第一次没有登录态时，会自动打开可见浏览器让用户登录。
- 默认读取 DM，但只读取浏览器页面上可见的内容。
- 支持 `--non-interactive`，定时任务遇到 passcode 时跳过 DM 恢复并记录数据缺口，不阻塞等待。
- 不自动发送消息、回复、点赞、关注、拉黑、打开可疑链接或接受 DM 请求。
- 只生成摘要和建议回复草稿。
- DM 原文只用于当次总结，不写入长期状态文件。

## 4. 首次运行流程

1. 用户运行：

   ```bash
   python3 twitter-digest/scripts/run_daily_digest.py
   ```

2. 脚本先尝试用 headless 浏览器读取保存的登录态。

3. 如果没有登录态，脚本自动打开可见浏览器窗口。

4. 用户在该浏览器窗口里登录 X。

5. 脚本检测登录成功。

6. 脚本自动识别当前 X 账号 handle。

7. 脚本采集 timeline、mentions、own profile、DM。

8. 脚本生成 `twitter-digest/.state/run/*` 当次采集文件。

9. Agent 只读取 `twitter-digest/.state/run/digest-context.md` 生成中文日报。

10. `digest-input.*` 只在排查抓取问题时使用。

## 5. 后续运行流程

1. 用户再次运行：

   ```bash
   python3 twitter-digest/scripts/run_daily_digest.py
   ```

2. 脚本默认 headless 启动。

3. 脚本复用：

   ```text
   twitter-digest/.state/chrome-profile
   ```

4. 如果登录态有效，不弹浏览器窗口。

5. 脚本直接采集并生成日报输入文件。

6. Agent 生成中文日报。

## 6. 需要人工介入的情况

以下情况会打开可见浏览器窗口：

- 第一次使用，还没有登录态。
- X session 过期。
- 用户退出了 X。
- X 要求 CAPTCHA 或风控验证。
- X Chat 要求设置或输入 passcode，此时会自动打开可见浏览器窗口，等待用户处理后继续。
- `twitter-digest/.state/chrome-profile` 被删除。

## 7. DM 规则

DM 默认读取。

读取范围：

- 只读 X Messages 通过浏览器加载出来的内容；打开等我回复会话后会自动向上滚动加载更多消息。
- 只统计今天可见会话数量、最后我发出的数量、等我回复的数量；列表里更早的历史会话不计入日报会话数。
- “最后我发出”只看 X Chat 列表最后预览是否是 `You:` / `You sent` / `你:`，不是指会话历史里曾经回复过。
- 消息数量单独统计，只来自已打开的等我回复会话里的消息气泡，不能和会话数量混用。
- 默认每个等我回复会话会尽量向上滚到对话顶部，完整捕获浏览器可加载的会话历史。
- 默认安全上限是向上滚动 200 次，并最多保留 2000 条消息气泡；`--dm-window-hours 0` 表示不按 24 小时窗口截断 DM 历史。
- 如果没有滚到顶部或命中消息上限，会在 `digest-context` 的数据缺口里记录 `dm_thread_incomplete`，不能假装完整。
- `digest-context.md` 会为需要总结的等我回复会话输出 `DM Thread Context`，最多带 2000 条已加载消息，并保留 raw label、URL、加载状态等原始信息，方便模型理解复杂上下文。
- 默认只打开今天等我回复的会话。
- 发信人以 `participant` / `会话对象` 和消息气泡方向为准，不能把引用帖、转发卡片、链接预览里的作者当作 DM 发信人。
- 如果今天可见会话最后一条都是我发出的，会记录 `no_unreplied_threads`，日报应写“今天可见私信会话最后一条都是我发出的，无需处理”，不能写“没有私信”。
- 如果能看到会话列表但打不开等我回复的正文，会记录 `visible_threads_unopened`。
- 只有 `captured_unreplied_threads` 的私信，才进入 DM 摘要。
- 等我回复的私信也要挑重点总结；垃圾、钓鱼、低质营销、重复无关内容只计数并归为忽略，不要展开正文。
- 如果 inbox 为空，会记录 `no_visible_threads`。
- 如果 X Chat 要求 passcode，headless 会自动切到可见浏览器窗口，等待用户输入或完成设置后重试 DM 采集。

隐私规则：

- 不长期保存 DM 原文。
- 不写 `memory.json`。
- 不写 `daily/` 历史归档。
- 不保存 DM thread 状态签名。

不保存：

- DM 原文
- X cookie
- token
- passcode
- 浏览器截图

## 8. 常用命令

生成今日 X 日报：

```bash
python3 twitter-digest/scripts/run_daily_digest.py
```

跳过 DM：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --no-dms
```

强制显示浏览器窗口：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --headed
```

无人值守定时运行：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --non-interactive
```

增加滚动覆盖：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --scrolls 5
```

增加关键词搜索：

```bash
python3 twitter-digest/scripts/run_daily_digest.py --keywords "AI,crypto"
```

清理登录状态并重新登录：

```bash
rm -rf twitter-digest/.state/chrome-profile
```

## 10. 预期日报结构

日报默认用中文输出：

```markdown
## 🐦 X 日报 - YYYY-MM-DD

**📌 今日总结**

**✅ 该处理**

**◆ 谁 @ 了你**

**◆ 私信（DM）**

**◆ 时间线热点**

**◆ 你的动态**

**✍️ 建议回复草稿**

**⚠️ 数据缺口**
```

## 11. PM 测试路径

1. 拉取分支：

   ```bash
   git clone git@github.com:BofAI/skills.git
   cd skills/skills
   git checkout twitter-digest-skill
   ```

2. 运行：

   ```bash
   python3 twitter-digest/scripts/run_daily_digest.py
   ```

3. 第一次弹浏览器时登录 X。

4. 等脚本完成。

5. 检查输出：

   ```text
   twitter-digest/.state/run/digest-context.md
   ```

   生成日报只读 `digest-context.md`。`digest-input.*` 只给开发排查抓取问题。

6. 再运行一次同样命令，确认后续默认 headless，不再弹浏览器窗口。
