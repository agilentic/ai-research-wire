#!/usr/bin/env python3
"""Prepare the static research site from Markdown source-of-truth files."""
from __future__ import annotations
import json, re, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "research" / "posts"
CONTENT = ROOT / "src" / "content" / "research"
DATA = ROOT / "data" / "articles.json"
PUBLIC = ROOT / "public" / "articles.json"
REQUIRED = {"title", "description", "date", "tags", "category", "status"}
def parse_frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not match: raise SystemExit(f"Missing YAML frontmatter: {path}")
    meta = {}
    for raw in match.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or ':' not in line: continue
        key, value = line.split(':', 1); value = value.strip()
        if value.startswith('[') and value.endswith(']'):
            meta[key.strip()] = [item.strip().strip('"\'') for item in value[1:-1].split(',') if item.strip()]
        elif value.lower() in {'true','false'}: meta[key.strip()] = value.lower() == 'true'
        else: meta[key.strip()] = value.strip('"\'')
    missing = REQUIRED - meta.keys()
    if missing: raise SystemExit(f"{path} missing frontmatter keys: {sorted(missing)}")
    return meta, match.group(2)
def estimate_reading_time(body: str) -> str:
    words = re.findall(r"\w+", body); return f"{max(1, round(len(words)/220))} min read"
def main():
    POSTS.mkdir(parents=True, exist_ok=True); CONTENT.mkdir(parents=True, exist_ok=True); DATA.parent.mkdir(parents=True, exist_ok=True)
    for old in CONTENT.glob('*.md'): old.unlink()
    articles=[]
    for path in sorted(POSTS.glob('*.md')):
        meta, body = parse_frontmatter(path); slug = path.stem; meta.setdefault('readingTime', estimate_reading_time(body)); shutil.copy2(path, CONTENT/path.name)
        articles.append({"slug":slug,"title":meta["title"],"description":meta["description"],"date":meta["date"],"updated":meta.get("updated"),"tags":meta.get("tags",[]),"category":meta["category"],"status":meta["status"],"featured":bool(meta.get("featured",False)),"readingTime":meta.get("readingTime"),"url":f"/research/{slug}/"})
    articles.sort(key=lambda item:item["date"], reverse=True)
    payload=json.dumps(articles, indent=2, ensure_ascii=False)+"\n"; DATA.write_text(payload, encoding="utf-8"); PUBLIC.write_text(payload, encoding="utf-8")
    print(f"Prepared {len(articles)} article(s).")
if __name__ == "__main__": main()
