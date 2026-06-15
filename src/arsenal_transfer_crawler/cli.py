from __future__ import annotations

import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import load_config
from .crawler import collect_news
from .emailer import render_report, send_email


def run_once(config_path: str | None, output: str | None, dry_run: bool) -> None:
    config = load_config(config_path)
    items, errors = collect_news(config.sources, config.lookback_hours, config.max_items)
    html = render_report(items, errors)
    if output:
        Path(output).write_text(html, encoding="utf-8")
    if dry_run:
        print(f"Collected {len(items)} items; email not sent because --dry-run was used.")
        for error in errors:
            print(f"WARNING: {error}")
        return
    send_email(config.recipient, html)
    print(f"Sent {len(items)} Arsenal transfer items to {config.recipient}.")


def _seconds_until(send_time: str, timezone: str) -> float:
    hour, minute = [int(part) for part in send_time.split(":", 1)]
    now = datetime.now(ZoneInfo(timezone))
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def schedule(config_path: str | None) -> None:
    config = load_config(config_path)
    print(f"Scheduled daily Arsenal transfer digest for {config.send_time} {config.timezone}.")
    while True:
        time.sleep(_seconds_until(config.send_time, config.timezone))
        run_once(config_path, None, False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Arsenal transfer news and email a clear daily digest.")
    parser.add_argument("--config", help="Path to YAML config. Defaults are used when omitted.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    once = subparsers.add_parser("once", help="Collect and send one report now.")
    once.add_argument("--dry-run", action="store_true", help="Collect and render without sending email.")
    once.add_argument("--output", help="Write rendered HTML report to this path.")

    subparsers.add_parser("schedule", help="Run continuously and send the report daily at the configured time.")
    args = parser.parse_args()

    if args.command == "once":
        run_once(args.config, args.output, args.dry_run)
    else:
        schedule(args.config)


if __name__ == "__main__":
    main()
