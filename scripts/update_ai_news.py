#!/usr/bin/env python3
"""Fetch AI-news feeds and publish a dated Markdown brief for the site.

The script is intentionally dependency-free so GitHub Actions can run it on a
plain Python runner. It treats RSS/Atom feeds as source material, deduplicates
links, and writes one Markdown article per UTC day under research/posts/.
"""
from __future__ import annotations

import argparse
import email.utils
import html
import json
import re
import sys
import textwrap
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "ai_news_sources.json"
POSTS = ROOT / "research" / "posts"
USER_AGENT = "Agilentic-AI-Research-Wire/1.0 (+https://github.com/agilentic/ai-research-wire)"
DEFAULT_MAX_ITEMS = 12
DEFAULT_PER_SOURCE_LIMIT = 4


@dataclass(slots=True)
class FeedItem:
    title: str
    link: str
    source: str
    published: datetime
    summary: str = ""
    tags: set[str] = field(default_factory=set)


def clean_text(value: str | None, max_len: int | None = None) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    if max_len and len(value) > max_len:
        return value[: max_len - 1].rsplit(" ", 1)[0] + "…"
    return value


def parse_date(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    value = value.strip()
    parsed = email.utils.parsedate_to_datetime(value)
    if parsed is not None:
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    # A small fallback for common Atom ISO-8601 variants.
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def xml_text(node: ET.Element, names: Iterable[str]) -> str:
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return found.text
    return ""


def atom_link(node: ET.Element) -> str:
    for link in node.findall("{http://www.w3.org/2005/Atom}link") + node.findall("link"):
        href = link.attrib.get("href")
        rel = link.attrib.get("rel", "alternate")
        if href and rel in {"alternate", ""}:
            return href
    return ""


def fetch_feed(source: dict) -> list[FeedItem]:
    req = urllib.request.Request(source["url"], headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = response.read()
    root = ET.fromstring(data)
    entries = root.findall(".//item") or root.findall("{http://www.w3.org/2005/Atom}entry")
    items: list[FeedItem] = []
    for entry in entries:
        title = clean_text(xml_text(entry, ["title", "{http://www.w3.org/2005/Atom}title"]))
        link = clean_text(xml_text(entry, ["link"])) or atom_link(entry)
        published_raw = xml_text(entry, [
            "pubDate",
            "published",
            "updated",
            "{http://www.w3.org/2005/Atom}published",
            "{http://www.w3.org/2005/Atom}updated",
        ])
        summary = clean_text(xml_text(entry, [
            "description",
            "summary",
            "content",
            "{http://www.w3.org/2005/Atom}summary",
            "{http://www.w3.org/2005/Atom}content",
        ]), max_len=280)
        if not title or not link:
            continue
        items.append(
            FeedItem(
                title=title,
                link=link,
                source=source["name"],
                published=parse_date(published_raw).astimezone(timezone.utc),
                summary=summary,
                tags=set(source.get("tags", [])),
            )
        )
    return items


def load_items() -> tuple[list[FeedItem], list[str]]:
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    items: list[FeedItem] = []
    errors: list[str] = []
    for source in sources:
        try:
            items.extend(fetch_feed(source))
        except (urllib.error.URLError, TimeoutError, ET.ParseError, KeyError, ValueError) as exc:
            errors.append(f"{source.get('name', source.get('url', 'unknown source'))}: {exc}")
    deduped: dict[str, FeedItem] = {}
    for item in items:
        key = re.sub(r"[#?].*$", "", item.link).rstrip("/")
        if key not in deduped or item.published > deduped[key].published:
            deduped[key] = item
    return sorted(deduped.values(), key=lambda x: x.published, reverse=True), errors


def select_items(items: list[FeedItem], max_items: int, per_source_limit: int) -> list[FeedItem]:
    """Keep the brief current without letting one high-volume feed dominate."""
    counts: dict[str, int] = {}
    selected: list[FeedItem] = []
    for item in items:
        if counts.get(item.source, 0) >= per_source_limit:
            continue
        selected.append(item)
        counts[item.source] = counts.get(item.source, 0) + 1
        if len(selected) >= max_items:
            break
    if len(selected) < max_items:
        seen = {item.link for item in selected}
        for item in items:
            if item.link in seen:
                continue
            selected.append(item)
            seen.add(item.link)
            if len(selected) >= max_items:
                break
    return selected


def write_markdown(items: list[FeedItem], errors: list[str], max_items: int, per_source_limit: int, date: str) -> Path:
    selected = select_items(items, max_items=max_items, per_source_limit=per_source_limit)
    if not selected:
        raise SystemExit("No feed items fetched; refusing to publish an empty AI-news brief.")
    slug = f"ai-news-wire-{date}"
    path = POSTS / f"{slug}.md"
    top_tags = sorted({tag for item in selected for tag in item.tags})[:8]
    tags = ["ai-news", "research-wire", *top_tags]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    newest = selected[0].published.strftime("%Y-%m-%d")
    sources = ", ".join(sorted({item.source for item in selected}))
    description = f"Automated AI news brief from {sources}. Newest source item: {newest}."

    lines = [
        "---",
        f'title: "AI News Wire — {date}"',
        f'description: "{description.replace(chr(34), chr(39))}"',
        f'date: "{date}"',
        f"tags: [{', '.join(tags)}]",
        'category: "AI News Briefs"',
        'status: "brief"',
        'author: "Agilentic News Bot"',
        "---",
        "",
        f"This automated brief was generated at **{now}** from public RSS/Atom feeds. It is a link digest, not an endorsement.",
        "",
        "## Top links",
        "",
    ]
    for idx, item in enumerate(selected, 1):
        stamp = item.published.strftime("%Y-%m-%d")
        lines.append(f"### {idx}. [{item.title}]({item.link})")
        lines.append(f"- **Source:** {item.source} · **Published:** {stamp}")
        if item.summary:
            wrapped = textwrap.fill(item.summary, width=96)
            lines.append(f"- **Feed summary:** {wrapped}")
        lines.append("")
    if errors:
        lines.extend(["## Feed warnings", ""])
        for error in errors:
            lines.append(f"- {error}")
        lines.append("")
    lines.extend([
        "## Automation note",
        "",
        "The GitHub Actions workflow `.github/workflows/ai-news.yml` refreshes this series on a schedule, commits new Markdown briefs, and then the Pages workflow rebuilds the public website.",
        "",
    ])
    POSTS.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish a dated AI-news brief from RSS/Atom feeds.")
    parser.add_argument("--date", default=datetime.now(timezone.utc).date().isoformat(), help="UTC date for the generated post slug/frontmatter")
    parser.add_argument("--max-items", type=int, default=DEFAULT_MAX_ITEMS, help="Maximum feed items to include")
    parser.add_argument("--per-source-limit", type=int, default=DEFAULT_PER_SOURCE_LIMIT, help="Maximum items to include from a single feed before filling remaining slots")
    args = parser.parse_args()
    items, errors = load_items()
    path = write_markdown(items, errors, args.max_items, args.per_source_limit, args.date)
    if errors:
        print("Feed warnings:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
    print(f"Wrote {path.relative_to(ROOT)} with {min(len(items), args.max_items)} item(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
