#!/usr/bin/env python3
"""Run API-vs-browser collection comparison rounds and archive reports."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from digest_context import build_current_context_from_file
from run_daily_digest import load_api_config, refresh_oauth_token_if_needed


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / ".state" / "compare-runs"
MIN_INTERVAL_SEC = 120
PUBLIC_KINDS = ["home", "own_profile", "mentions_search", "mentions_notifications"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=3, help="Number of comparison rounds.")
    parser.add_argument("--interval-sec", type=int, default=MIN_INTERVAL_SEC, help="Delay between rounds. Values below 120 are raised to 120.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT), help="Directory for archived comparison runs.")
    parser.add_argument("--handle", default="", help="Optional X handle override.")
    parser.add_argument("--keywords", default="", help="Optional comma-separated keyword searches.")
    parser.add_argument("--max-public-items", type=int, default=300)
    parser.add_argument("--public-window-hours", type=int, default=24)
    parser.add_argument("--scrolls", type=int, default=40)
    parser.add_argument("--dm-threads", type=int, default=5)
    parser.add_argument("--dm-scrolls", type=int, default=200)
    parser.add_argument("--dm-max-messages", type=int, default=2000)
    parser.add_argument("--dm-window-hours", type=int, default=0)
    parser.add_argument("--dm-max-events", type=int, default=300)
    parser.add_argument("--headed", action="store_true", help="Run browser collection in a visible browser window.")
    parser.add_argument("--headless", action="store_true", help="Force browser collection headless.")
    parser.add_argument("--non-interactive", action="store_true", help="Do not open visible browser recovery windows.")
    parser.add_argument("--skip-api", action="store_true", help="Only run browser collector; report API as skipped.")
    parser.add_argument("--skip-browser", action="store_true", help="Only run API collector; report browser as skipped.")
    return parser.parse_args()


def now_stamp() -> str:
    return dt.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def load_bearer_token() -> str:
    config = refresh_oauth_token_if_needed(load_api_config())
    return str(config.get("bearer_token") or os.environ.get("X_BEARER_TOKEN") or os.environ.get("TWITTER_BEARER_TOKEN") or "")


def run_command(cmd: list[str], out_dir: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    result = subprocess.run(cmd, text=True, capture_output=True, env=env)
    duration = time.time() - started
    (out_dir / "stdout.log").write_text(result.stdout, encoding="utf-8")
    (out_dir / "stderr.log").write_text(result.stderr, encoding="utf-8")
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "duration_sec": round(duration, 2),
        "error_summary": summarize_error(result.stderr or result.stdout),
    }


def summarize_error(text: str) -> str:
    if not text:
        return ""
    markers = [
        "client-not-enrolled",
        "Appropriate Level of API Access",
        "Unauthorized",
        "Forbidden",
        "HTTP 401",
        "HTTP 403",
        "HTTP 429",
        "Too Many Requests",
        "Timed out",
        "passcode",
    ]
    matched = [marker for marker in markers if marker in text]
    if matched:
        return "; ".join(dict.fromkeys(matched))
    return " ".join(text.split())[:500]


def api_command(args: argparse.Namespace, out_dir: Path) -> tuple[list[str], dict[str, str]]:
    token = load_bearer_token()
    env = os.environ.copy()
    if token:
        env["X_BEARER_TOKEN"] = token
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "api_x_digest.py"),
        "--out",
        str(out_dir),
        "--keywords",
        args.keywords,
        "--max-public-items",
        str(args.max_public_items),
        "--public-window-hours",
        str(args.public_window_hours),
        "--dm-max-events",
        str(args.dm_max_events),
        "--include-dms",
    ]
    if args.handle:
        cmd.extend(["--handle", args.handle.lstrip("@")])
    return cmd, env


def browser_command(args: argparse.Namespace, out_dir: Path) -> list[str]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "browser_x_digest.py"),
        "--out",
        str(out_dir),
        "--keywords",
        args.keywords,
        "--max-public-items",
        str(args.max_public_items),
        "--public-window-hours",
        str(args.public_window_hours),
        "--scrolls",
        str(args.scrolls),
        "--dm-threads",
        str(args.dm_threads),
        "--dm-scrolls",
        str(args.dm_scrolls),
        "--dm-max-messages",
        str(args.dm_max_messages),
        "--dm-window-hours",
        str(args.dm_window_hours),
        "--include-dms",
    ]
    if args.handle:
        cmd.extend(["--handle", args.handle.lstrip("@")])
    if args.headed:
        cmd.append("--headed")
    if args.headless:
        cmd.append("--headless")
    if args.non_interactive:
        cmd.append("--non-interactive")
    return cmd


def build_context_if_possible(out_dir: Path) -> None:
    input_json = out_dir / "digest-input.json"
    if input_json.exists():
        build_current_context_from_file(input_json, out_dir, out_dir / "digest-input.md")


def load_digest(out_dir: Path) -> dict[str, Any]:
    path = out_dir / "digest-input.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def page_by_kind(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pages = {}
    for page in data.get("pages") or []:
        if isinstance(page, dict):
            pages[str(page.get("kind") or "unknown")] = page
    return pages


def item_keys(page: dict[str, Any]) -> set[str]:
    keys = set()
    for item in page.get("items") or []:
        if not isinstance(item, dict):
            continue
        key = str(item.get("url") or item.get("time") or "") + "\n" + str(item.get("text") or "")[:160]
        if key.strip():
            keys.add(key)
    return keys


def source_summary(name: str, out_dir: Path, run_result: dict[str, Any]) -> dict[str, Any]:
    data = load_digest(out_dir)
    pages = page_by_kind(data)
    page_counts = {
        kind: len(page.get("items") or [])
        for kind, page in pages.items()
        if kind != "messages"
    }
    messages = pages.get("messages") or {}
    return {
        "source": name,
        "ok": run_result.get("ok", False),
        "returncode": run_result.get("returncode"),
        "duration_sec": run_result.get("duration_sec"),
        "error_summary": run_result.get("error_summary", ""),
        "handle": data.get("handle") or "",
        "generated_at": data.get("generated_at") or "",
        "page_counts": page_counts,
        "dm": {
            "status": messages.get("dm_status") or "not_present",
            "today_visible": int(messages.get("dm_visible_thread_count") or 0),
            "last_from_me": int(messages.get("dm_replied_thread_count") or 0),
            "waiting_reply": int(messages.get("dm_unreplied_thread_count") or 0),
            "captured_messages": int(messages.get("dm_captured_message_count") or 0),
            "note": messages.get("dm_note") or "",
        },
        "data_gaps": collect_data_gaps(out_dir),
    }


def collect_data_gaps(out_dir: Path) -> list[dict[str, Any]]:
    path = out_dir / "digest-context.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    facts = data.get("facts") if isinstance(data, dict) else {}
    gaps = facts.get("data_gaps") if isinstance(facts, dict) else []
    return gaps if isinstance(gaps, list) else []


def compare_sources(api_dir: Path, browser_dir: Path) -> dict[str, Any]:
    api_data = load_digest(api_dir)
    browser_data = load_digest(browser_dir)
    api_pages = page_by_kind(api_data)
    browser_pages = page_by_kind(browser_data)
    public = {}
    for kind in PUBLIC_KINDS:
        api_keys = item_keys(api_pages.get(kind) or {})
        browser_keys = item_keys(browser_pages.get(kind) or {})
        public[kind] = {
            "api_count": len(api_keys),
            "browser_count": len(browser_keys),
            "overlap": len(api_keys & browser_keys),
            "api_only": len(api_keys - browser_keys),
            "browser_only": len(browser_keys - api_keys),
        }
    api_messages = api_pages.get("messages") or {}
    browser_messages = browser_pages.get("messages") or {}
    return {
        "public": public,
        "dm": {
            "api_status": api_messages.get("dm_status") or "not_present",
            "browser_status": browser_messages.get("dm_status") or "not_present",
            "api_waiting_reply": int(api_messages.get("dm_unreplied_thread_count") or 0),
            "browser_waiting_reply": int(browser_messages.get("dm_unreplied_thread_count") or 0),
            "api_captured_messages": int(api_messages.get("dm_captured_message_count") or 0),
            "browser_captured_messages": int(browser_messages.get("dm_captured_message_count") or 0),
        },
    }


def run_round(args: argparse.Namespace, run_root: Path, index: int) -> dict[str, Any]:
    round_dir = run_root / f"round-{index:02d}"
    api_dir = round_dir / "api"
    browser_dir = round_dir / "browser"
    round_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"round": index, "started_at": dt.datetime.now().astimezone().isoformat()}

    if args.skip_api:
        api_result = {"ok": False, "returncode": None, "duration_sec": 0, "error_summary": "skipped"}
    else:
        cmd, env = api_command(args, api_dir)
        print(f"[round {index}] running API collector...", flush=True)
        api_result = run_command(cmd, api_dir, env=env)
        build_context_if_possible(api_dir)
    result["api"] = source_summary("api", api_dir, api_result)

    if args.skip_browser:
        browser_result = {"ok": False, "returncode": None, "duration_sec": 0, "error_summary": "skipped"}
    else:
        print(f"[round {index}] running browser collector...", flush=True)
        browser_result = run_command(browser_command(args, browser_dir), browser_dir)
        build_context_if_possible(browser_dir)
    result["browser"] = source_summary("browser", browser_dir, browser_result)
    result["comparison"] = compare_sources(api_dir, browser_dir)
    result["finished_at"] = dt.datetime.now().astimezone().isoformat()
    (round_dir / "round-summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (round_dir / "round-summary.md").write_text(render_round_markdown(result), encoding="utf-8")
    return result


def aggregate(rounds: list[dict[str, Any]], run_root: Path) -> dict[str, Any]:
    report = {
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "round_count": len(rounds),
        "rounds": rounds,
        "stability": {
            "api_success": sum(1 for item in rounds if item.get("api", {}).get("ok")),
            "browser_success": sum(1 for item in rounds if item.get("browser", {}).get("ok")),
            "api_errors": [item.get("api", {}).get("error_summary") for item in rounds if item.get("api", {}).get("error_summary")],
            "browser_errors": [item.get("browser", {}).get("error_summary") for item in rounds if item.get("browser", {}).get("error_summary")],
        },
        "completeness": aggregate_completeness(rounds),
    }
    (run_root / "comparison-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run_root / "comparison-report.md").write_text(render_report_markdown(report), encoding="utf-8")
    return report


def aggregate_completeness(rounds: list[dict[str, Any]]) -> dict[str, Any]:
    count = max(1, len(rounds))
    public: dict[str, dict[str, float | int]] = {}
    for kind in PUBLIC_KINDS:
        totals = {"api_count": 0, "browser_count": 0, "overlap": 0, "api_only": 0, "browser_only": 0}
        for item in rounds:
            diff = ((item.get("comparison") or {}).get("public") or {}).get(kind) or {}
            for key in totals:
                totals[key] += int(diff.get(key) or 0)
        public[kind] = {
            "avg_api_count": round(totals["api_count"] / count, 1),
            "avg_browser_count": round(totals["browser_count"] / count, 1),
            "avg_overlap": round(totals["overlap"] / count, 1),
            "avg_api_only": round(totals["api_only"] / count, 1),
            "avg_browser_only": round(totals["browser_only"] / count, 1),
            "rounds_api_empty": sum(
                1
                for item in rounds
                if int((((item.get("comparison") or {}).get("public") or {}).get(kind) or {}).get("api_count") or 0) == 0
            ),
            "rounds_browser_empty": sum(
                1
                for item in rounds
                if int((((item.get("comparison") or {}).get("public") or {}).get(kind) or {}).get("browser_count") or 0) == 0
            ),
        }
    return {
        "public": public,
        "dm_note": "Browser DM is authoritative for X Chat / encrypted conversations; API DM is TODO/debug only.",
    }


def render_round_markdown(result: dict[str, Any]) -> str:
    lines = [f"# Round {result.get('round')} Comparison", ""]
    for source in ("api", "browser"):
        item = result.get(source) or {}
        lines.extend(
            [
                f"## {source}",
                "",
                f"- ok: `{item.get('ok')}`",
                f"- duration_sec: `{item.get('duration_sec')}`",
                f"- error: {item.get('error_summary') or 'None'}",
                f"- page_counts: `{json.dumps(item.get('page_counts') or {}, ensure_ascii=False)}`",
                f"- dm: `{json.dumps(item.get('dm') or {}, ensure_ascii=False)}`",
                "",
            ]
        )
    lines.extend(["## Differences", "", "### Public", "", "| page | api | browser | overlap | api_only | browser_only |", "|---|---:|---:|---:|---:|---:|"])
    for kind, diff in ((result.get("comparison") or {}).get("public") or {}).items():
        lines.append(f"| {kind} | {diff['api_count']} | {diff['browser_count']} | {diff['overlap']} | {diff['api_only']} | {diff['browser_only']} |")
    dm = ((result.get("comparison") or {}).get("dm") or {})
    lines.extend(
        [
            "",
            "### DM",
            "",
            f"- API status: `{dm.get('api_status')}`",
            f"- Browser status: `{dm.get('browser_status')}`",
            f"- API waiting/captured: `{dm.get('api_waiting_reply')}` / `{dm.get('api_captured_messages')}`",
            f"- Browser waiting/captured: `{dm.get('browser_waiting_reply')}` / `{dm.get('browser_captured_messages')}`",
            "",
        ]
    )
    return "\n".join(lines)


def render_report_markdown(report: dict[str, Any]) -> str:
    rounds = report.get("rounds") or []
    stability = report.get("stability") or {}
    completeness = report.get("completeness") or {}
    lines = [
        "# X Digest Collector Comparison Report",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- rounds: `{report.get('round_count')}`",
        f"- api_success: `{stability.get('api_success')}` / `{report.get('round_count')}`",
        f"- browser_success: `{stability.get('browser_success')}` / `{report.get('round_count')}`",
        "",
        "## Round Summary",
        "",
        "| round | api_ok | browser_ok | api_home | browser_home | api_mentions | browser_mentions | api_dm | browser_dm |",
        "|---:|---|---|---:|---:|---:|---:|---|---|",
    ]
    for item in rounds:
        api = item.get("api") or {}
        browser = item.get("browser") or {}
        api_counts = api.get("page_counts") or {}
        browser_counts = browser.get("page_counts") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item.get("round")),
                    str(api.get("ok")),
                    str(browser.get("ok")),
                    str(api_counts.get("home", 0)),
                    str(browser_counts.get("home", 0)),
                    str(api_counts.get("mentions_notifications", 0) + api_counts.get("mentions_search", 0)),
                    str(browser_counts.get("mentions_notifications", 0) + browser_counts.get("mentions_search", 0)),
                    str((api.get("dm") or {}).get("status")),
                    str((browser.get("dm") or {}).get("status")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Aggregate Completeness",
            "",
            "| page | avg_api | avg_browser | avg_overlap | avg_api_only | avg_browser_only | api_empty_rounds | browser_empty_rounds |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for kind, diff in (completeness.get("public") or {}).items():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(kind),
                    str(diff.get("avg_api_count")),
                    str(diff.get("avg_browser_count")),
                    str(diff.get("avg_overlap")),
                    str(diff.get("avg_api_only")),
                    str(diff.get("avg_browser_only")),
                    str(diff.get("rounds_api_empty")),
                    str(diff.get("rounds_browser_empty")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Rules",
            "",
            "- API and browser public counts can differ because API returns structured endpoints while browser reads currently loaded UI.",
            "- Browser DM is authoritative for X Chat / encrypted conversations.",
            "- API DM `api_dm_todo` or zero events is not evidence of no DMs.",
            "- Review per-round `digest-input.json`, `digest-context.md`, `stdout.log`, and `stderr.log` before concluding a bug.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    interval = max(MIN_INTERVAL_SEC, int(args.interval_sec))
    rounds = max(1, int(args.rounds))
    run_root = Path(args.out_dir).expanduser().resolve() / now_stamp()
    run_root.mkdir(parents=True, exist_ok=True)
    try:
        run_root.chmod(0o700)
    except PermissionError:
        pass
    metadata = {
        "started_at": dt.datetime.now().astimezone().isoformat(),
        "rounds": rounds,
        "interval_sec": interval,
        "args": {key: value for key, value in vars(args).items() if key not in {"bearer_token"}},
    }
    (run_root / "run-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summaries = []
    for index in range(1, rounds + 1):
        summaries.append(run_round(args, run_root, index))
        if index < rounds:
            print(f"Waiting {interval} seconds before next round to reduce API rate-limit risk...", flush=True)
            time.sleep(interval)
    report = aggregate(summaries, run_root)
    print(json.dumps({"report_markdown": str(run_root / "comparison-report.md"), "report_json": str(run_root / "comparison-report.json"), "rounds": report["round_count"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
