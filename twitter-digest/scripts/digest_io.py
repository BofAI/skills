"""Shared digest input output contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from script_utils import ensure_private_dir


def write_digest_output(out_dir: Path, data: dict[str, Any]) -> None:
    ensure_private_dir(out_dir)
    (out_dir / "digest-input.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "digest-input.md").write_text(render_markdown(data), encoding="utf-8")


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
            lines.append(f"DM 消息统计: 已打开等我回复会话中捕获消息气泡 `{int(page.get('dm_captured_message_count') or 0)}`")
            if page.get("dm_note"):
                lines.append(str(page["dm_note"]))
        if page.get("collection_error"):
            lines.extend(["", f"采集错误: `{page['collection_error']}`"])
        for thread in page.get("dm_threads", [])[:20]:
            participant = thread.get("participant") or thread.get("label") or thread.get("url")
            lines.extend(["", f"### DM thread: {participant}", ""])
            if participant:
                lines.append(f"会话对象: `{participant}`")
                lines.append(f"会话状态: `{'最后我发出' if thread.get('replied') else '等我回复'}`")
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
            "- DM / X Chat 可能不会完整出现在 API 结果中；不要把 0 条 API DM 当作没有私信。",
            "- DM 属于私密内容，不写长期 memory 或 daily archive。",
        ]
    )
    return "\n".join(lines) + "\n"
