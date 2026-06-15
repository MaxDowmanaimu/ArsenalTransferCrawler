from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_RECIPIENT = "maxdowman1231@outlook.com"
TRANSFER_KEYWORDS = [
    "transfer", "sign", "signing", "signed", "deal", "bid", "offer", "target",
    "loan", "clause", "fee", "medical", "contract", "release clause", "interest",
    "linked", "joins", "exit", "move", "rumour", "rumor", "agrees",
]
ARSENAL_KEYWORDS = ["arsenal", "gunners", "mikel arteta", "emirates"]


@dataclass(frozen=True)
class SourceConfig:
    name: str
    url: str
    credibility: int
    include_keywords: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AppConfig:
    recipient: str = DEFAULT_RECIPIENT
    lookback_hours: int = 24
    max_items: int = 25
    timezone: str = "Europe/London"
    send_time: str = "08:00"
    sources: list[SourceConfig] = field(default_factory=list)


def default_sources() -> list[SourceConfig]:
    return [
        SourceConfig("Arsenal.com", "https://www.arsenal.com/news/rss", 100),
        SourceConfig("BBC Sport - Arsenal", "https://feeds.bbci.co.uk/sport/football/rss.xml", 92, ["Arsenal", "Gunners", "transfer", "signing", "loan"]),
        SourceConfig("Sky Sports - Arsenal", "https://www.skysports.com/rss/12040", 88),
        SourceConfig("The Guardian - Arsenal", "https://www.theguardian.com/football/arsenal/rss", 86),
        SourceConfig("ESPN FC - Arsenal", "https://www.espn.com/espn/rss/soccer/news", 78, ["Arsenal", "Gunners"]),
    ]


def _parse_scalar(value: str) -> Any:
    value = value.strip().strip('"').strip("'")
    if value.startswith("[") and value.endswith("]"):
        return [part.strip().strip('"').strip("'") for part in value[1:-1].split(",") if part.strip()]
    if value.isdigit():
        return int(value)
    return value


def _load_simple_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    sources: list[dict[str, Any]] = []
    current_source: dict[str, Any] | None = None
    in_sources = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("sources:"):
            in_sources = True
            data["sources"] = sources
            continue
        if in_sources:
            stripped = line.strip()
            if stripped.startswith("- "):
                current_source = {}
                sources.append(current_source)
                stripped = stripped[2:]
            if current_source is not None and ":" in stripped:
                key, value = stripped.split(":", 1)
                current_source[key.strip()] = _parse_scalar(value)
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = _parse_scalar(value)
    return data


def load_config(path: str | Path | None = None) -> AppConfig:
    raw: dict[str, Any] = {}
    if path:
        config_path = Path(path)
        if config_path.exists():
            raw = _load_simple_yaml(config_path)

    sources_raw = raw.get("sources") or []
    sources = [SourceConfig(**item) for item in sources_raw] if sources_raw else default_sources()
    return AppConfig(
        recipient=raw.get("recipient", DEFAULT_RECIPIENT),
        lookback_hours=int(raw.get("lookback_hours", 24)),
        max_items=int(raw.get("max_items", 25)),
        timezone=raw.get("timezone", "Europe/London"),
        send_time=raw.get("send_time", "08:00"),
        sources=sources,
    )
