#!/usr/bin/env python3
"""Create or update a research post and its metadata.

This script is intentionally local/Git-first. Hermes can call it after researching a
Telegram-requested topic, then run build checks and open a PR.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "research" / "posts"
DATA = ROOT / "data" / "articles.json"
CATEGORIES = ["AI labs", "model releases", "agentic workflows", "scientific papers", "infra", "safety", "startups"]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a Markdown research essay into AI Research Wire")
    parser.add_argument("--title", required=True)
    parser.add_argument("--category", required=True, choices=CATEGORIES)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--body-file", help="Markdown body file. If omitted, a starter draft is created.")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--status", default="published", choices=["draft", "published"])
    parser.add_argument("--slug")
    args = parser.parse_args()

    slug = args.slug or slugify(args.title)
    POSTS.mkdir(parents=True, exist_ok=True)
    post_path = POSTS / f"{slug}.md"
    if args.body_file:
        body = Path(args.body_file).read_text()
    else:
        body = f"# {args.title}\n\n## Abstract\n\n{args.summary}\n\n## Notes\n\n- Replace this starter with Hermes research and cited sources.\n"
    frontmatter = f"---\ntitle: {args.title}\nslug: {slug}\ndate: {args.date}\ncategory: {args.category}\nstatus: {args.status}\n---\n\n"
    post_path.write_text(frontmatter + body.lstrip())

    articles = json.loads(DATA.read_text()) if DATA.exists() else []
    record = {
        "slug": slug,
        "title": args.title,
        "date": args.date,
        "category": args.category,
        "summary": args.summary,
        "status": args.status,
        "featured": False,
        "reading_time": "auto",
        "sources": []
    }
    updated = False
    for i, article in enumerate(articles):
        if article.get("slug") == slug:
            articles[i] = {**article, **record}
            updated = True
            break
    if not updated:
        articles.append(record)
    articles.sort(key=lambda item: item["date"], reverse=True)
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(articles, indent=2) + "\n")
    print(f"Wrote {post_path} and updated {DATA}")


if __name__ == "__main__":
    main()
