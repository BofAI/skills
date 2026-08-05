"""Shared digest input output contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from script_utils import ensure_private_dir, write_private_text


def write_digest_output(out_dir: Path, data: dict[str, Any]) -> None:
    ensure_private_dir(out_dir)
    write_private_text(out_dir / "digest-input.json", json.dumps(data, ensure_ascii=False, indent=2))
    write_private_text(out_dir / "digest-input.md", render_markdown(data))


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# X 采集输入",
        "",
        f"- 生成时间: `{data['generated_at']}`",
        f"- 数据源: `{data.get('source') or 'api'}`",
        f"- 当前账号: `{data.get('handle') or ''}`",
        "",
    ]
    for page in data["pages"]:
        lines.extend([f"## {page['kind']}", "", f"Source: {page['url']}", ""])
        lines.append(f"采集条数: `{len(page.get('items', []))}`")
        lines.append("")
        for item in page["items"][:80]:
            text = " ".join(str(item.get("text") or "").split())
            url = item.get("url") or ""
            timestamp = item.get("time") or ""
            lines.append(f"- `{timestamp}` {url}")
            lines.append(f"  {text[:1000]}")
        if page.get("visible_text"):
            lines.extend(["", "页面可见文本摘录:", "", str(page["visible_text"])[:3000]])
        if page.get("dm_status"):
            lines.extend(["", f"DM 状态: `{page['dm_status']}`"])
            lines.append(
                "DM 会话统计: "
                f"今日可见 `{int(page.get('dm_visible_thread_count') or 0)}` / "
                f"最后我发出 `{int(page.get('dm_replied_thread_count') or 0)}` / "
                f"等我回复 `{int(page.get('dm_unreplied_thread_count') or 0)}`"
            )
            lines.append(f"状态未知会话: `{int(page.get('dm_unknown_thread_count') or 0)}`")
            lines.append(f"DM 消息统计: 当前窗口内捕获消息 `{int(page.get('dm_captured_message_count') or 0)}`")
            lines.append(f"Chat 请求: `{'有待处理请求' if page.get('dm_has_message_requests') else '无'}`")
            if page.get("dm_note"):
                lines.append(str(page["dm_note"]))
        if page.get("collection_error"):
            lines.extend(["", f"采集错误: `{page['collection_error']}`"])
        for thread in page.get("dm_threads", [])[:20]:
            participant = thread.get("participant") or thread.get("label") or thread.get("url")
            lines.extend(["", f"### DM thread: {participant}", ""])
            if participant:
                lines.append(f"会话对象: `{participant}`")
                reply_state = str(thread.get("reply_state") or ("最后我发出" if thread.get("replied") else "等我回复"))
                lines.append(f"会话状态: `{reply_state}`")
                if thread.get("collection_detail"):
                    lines.append(f"采集说明: {thread.get('collection_detail')}")
                lines.append(f"消息数量: `{int(thread.get('message_count') or 0)}`")
                lines.append("发信人判断: 使用会话对象/消息气泡判断；引用帖、转发卡片或链接预览里的作者不是 DM 发信人。")
                lines.append("")
            lines.append(str(thread.get("text") or "")[:3000])
        lines.append("")
    lines.extend(
        [
            "## 数据缺口",
            "",
            "- API 采集受 X API 权限、套餐、端点可用性和限流影响。",
            "- X Chat 由官方 Chat API 提供，并在本地通过 Chat XDK 解密；采集或解密失败时整次日报失败。",
            "- DM 属于私密内容，不写长期 memory 或 daily archive。",
        ]
    )
    return "\n".join(lines) + "\n"
