from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from .config import ARSENAL_KEYWORDS, TRANSFER_KEYWORDS, SourceConfig

USER_AGENT = "ArsenalTransferCrawler/0.1 (+https://github.com/)"


@dataclass(frozen=True)
class NewsItem:
    title: str
    link: str
    source: str
    credibility: int
    published: datetime | None
    summary: str
    score: int


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    folded = text.casefold()
    return any(keyword.casefold() in folded for keyword in keywords)


def _published(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def _clean(value: str | None) -> str:
    text = unescape(value or "")
    out: list[str] = []
    in_tag = False
    for char in text:
        if char == "<":
            in_tag = True
        elif char == ">":
            in_tag = False
        elif not in_tag:
            out.append(char)
    return " ".join("".join(out).split())


def _child_text(element: ElementTree.Element, names: tuple[str, ...]) -> str:
    for child in element.iter():
        tag = child.tag.rsplit("}", 1)[-1].casefold()
        if tag in names and child.text:
            return child.text
    return ""


def _relevance_score(title: str, summary: str, credibility: int) -> int:
    text = f"{title} {summary}".casefold()
    keyword_hits = sum(1 for word in TRANSFER_KEYWORDS if word.casefold() in text)
    return credibility * 10 + min(keyword_hits, 8) * 12


def fetch_source(source: SourceConfig, lookback_hours: int) -> list[NewsItem]:
    request = Request(source.url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=20) as response:
        xml = response.read()
    root = ElementTree.fromstring(xml)
    entries = [item for item in root.iter() if item.tag.rsplit("}", 1)[-1].casefold() in {"item", "entry"}]
    cutoff = datetime.now(UTC) - timedelta(hours=lookback_hours)
    items: list[NewsItem] = []

    for entry in entries:
        title = _clean(_child_text(entry, ("title",)))
        summary = _clean(_child_text(entry, ("description", "summary", "content")))
        link = _child_text(entry, ("link",))
        published = _published(_child_text(entry, ("pubdate", "published", "updated")))
        haystack = f"{title} {summary}"

        if published and published < cutoff:
            continue
        if source.include_keywords and not _contains_any(haystack, source.include_keywords):
            continue
        if not _contains_any(haystack, ARSENAL_KEYWORDS):
            continue
        if not _contains_any(haystack, TRANSFER_KEYWORDS):
            continue

        items.append(NewsItem(title, link, source.name, source.credibility, published, summary[:500], _relevance_score(title, summary, source.credibility)))
    return items


def collect_news(sources: list[SourceConfig], lookback_hours: int, max_items: int) -> tuple[list[NewsItem], list[str]]:
    seen: set[str] = set()
    collected: list[NewsItem] = []
    errors: list[str] = []
    for source in sources:
        try:
            for item in fetch_source(source, lookback_hours):
                dedupe_key = item.link or item.title.casefold()
                if dedupe_key not in seen:
                    seen.add(dedupe_key)
                    collected.append(item)
        except (URLError, TimeoutError, ElementTree.ParseError) as exc:
            errors.append(f"{source.name}: {exc}")
    collected.sort(key=lambda item: (item.score, item.published or datetime.min.replace(tzinfo=UTC)), reverse=True)
    return collected[:max_items], errors
