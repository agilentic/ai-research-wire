#!/usr/bin/env python3
"""Build AI Research Wire into static HTML for GitHub Pages."""
from __future__ import annotations

import html
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "research" / "posts"
DATA_FILE = ROOT / "data" / "articles.json"
PUBLIC = ROOT / "public"
ASSETS = ROOT / "assets"
CATEGORIES = ["AI labs", "model releases", "agentic workflows", "scientific papers", "infra", "safety", "startups"]


@dataclass
class Article:
    slug: str
    title: str
    date: str
    category: str
    summary: str
    status: str
    featured: bool
    reading_time: str
    sources: list[dict[str, str]]
    markdown: str
    body_html: str
    toc: list[tuple[str, str, int]]


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "section"


def strip_frontmatter(markdown: str) -> str:
    if markdown.startswith("---\n"):
        end = markdown.find("\n---\n", 4)
        if end != -1:
            return markdown[end + 5 :].lstrip()
    return markdown


def inline_markdown(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def markdown_to_html(markdown: str) -> tuple[str, list[tuple[str, str, int]]]:
    markdown = strip_frontmatter(markdown)
    lines = markdown.splitlines()
    output: list[str] = []
    toc: list[tuple[str, str, int]] = []
    paragraph: list[str] = []
    in_list = False
    in_code = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            output.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                output.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines = []
                in_code = False
            else:
                flush_paragraph(); close_list(); in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            flush_paragraph(); close_list(); continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            flush_paragraph(); close_list()
            level = len(heading.group(1))
            text = heading.group(2).strip()
            ident = slugify(text)
            toc.append((ident, text, level))
            output.append(f'<h{level} id="{ident}">{inline_markdown(text)}</h{level}>')
            continue
        if line.startswith("- "):
            flush_paragraph()
            if not in_list:
                output.append("<ul>"); in_list = True
            output.append(f"<li>{inline_markdown(line[2:].strip())}</li>")
            continue
        if re.match(r"^\d+\.\s+", line):
            # Render ordered-ish source as paragraph-friendly unordered list for simplicity.
            flush_paragraph()
            if not in_list:
                output.append("<ul>"); in_list = True
            output.append(f"<li>{inline_markdown(re.sub(r'^\d+\.\s+', '', line).strip())}</li>")
            continue
        if line.startswith("> "):
            flush_paragraph(); close_list()
            output.append(f"<blockquote>{inline_markdown(line[2:].strip())}</blockquote>")
            continue
        paragraph.append(line.strip())
    flush_paragraph(); close_list()
    return "\n".join(output), toc


def load_articles() -> list[Article]:
    metadata: list[dict[str, Any]] = json.loads(DATA_FILE.read_text())
    articles: list[Article] = []
    seen = set()
    for item in metadata:
        slug = item["slug"]
        if slug in seen:
            raise ValueError(f"duplicate article slug: {slug}")
        seen.add(slug)
        category = item.get("category", "")
        if category not in CATEGORIES:
            raise ValueError(f"{slug}: unknown category {category!r}; use one of {CATEGORIES}")
        md_path = POSTS_DIR / f"{slug}.md"
        if not md_path.exists():
            raise FileNotFoundError(f"metadata references missing post: {md_path}")
        markdown = md_path.read_text()
        body_html, toc = markdown_to_html(markdown)
        articles.append(Article(
            slug=slug,
            title=item["title"],
            date=item["date"],
            category=category,
            summary=item.get("summary", ""),
            status=item.get("status", "draft"),
            featured=bool(item.get("featured", False)),
            reading_time=item.get("reading_time", estimate_reading_time(markdown)),
            sources=item.get("sources", []),
            markdown=markdown,
            body_html=body_html,
            toc=toc,
        ))
    return sorted([a for a in articles if a.status == "published"], key=lambda a: a.date, reverse=True)


def estimate_reading_time(text: str) -> str:
    words = len(re.findall(r"\w+", strip_frontmatter(text)))
    return f"{max(1, round(words / 220))} min"


def site_head(title: str, description: str, url_path: str = "") -> str:
    canonical = f"https://agilentic.github.io/ai-research-wire/{url_path}".rstrip("/") + "/"
    return f"""<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>{html.escape(title)}</title>
<meta name=\"description\" content=\"{html.escape(description)}\">
<link rel=\"canonical\" href=\"{canonical}\">
<link rel=\"stylesheet\" href=\"/ai-research-wire/assets/styles.css\">
<script defer src=\"/ai-research-wire/assets/site.js\"></script>
<meta property=\"og:title\" content=\"{html.escape(title)}\">
<meta property=\"og:description\" content=\"{html.escape(description)}\">
<meta property=\"og:type\" content=\"website\">
<meta name=\"twitter:card\" content=\"summary_large_image\">
<script type=\"application/ld+json\">{{"@context":"https://schema.org","@type":"WebSite","name":"AI Research Wire","url":"https://agilentic.github.io/ai-research-wire/"}}</script>"""


def chrome(content: str, *, title: str, description: str, url_path: str = "") -> str:
    return f"""<!doctype html>
<html lang=\"en\" data-theme=\"light\">
<head>{site_head(title, description, url_path)}</head>
<body>
  <div class=\"site-shell\">
    <header class=\"site-header\">
      <a class=\"brand\" href=\"/ai-research-wire/\"><span class=\"brand-mark\">AI↯RW</span><span class=\"brand-text\">AI Research Wire</span></a>
      <nav class=\"nav\" aria-label=\"Primary\">
        <a href=\"/ai-research-wire/\">Home</a>
        <a href=\"/ai-research-wire/feed.xml\">RSS</a>
        <a href=\"/ai-research-wire/llms.txt\">llms.txt</a>
        <a href=\"https://github.com/agilentic/ai-research-wire\">GitHub</a>
        <button class=\"theme-toggle\" data-theme-toggle type=\"button\">Theme</button>
      </nav>
    </header>
    {content}
    <footer class=\"footer\">GitHub is the source of truth. Articles are Markdown in <code>research/posts</code>; metadata lives in <code>data/articles.json</code>.</footer>
  </div>
</body>
</html>"""


def render_home(articles: list[Article]) -> str:
    featured = next((a for a in articles if a.featured), articles[0] if articles else None)
    category_buttons = "\n".join(f'<button class="filter" data-filter="{html.escape(c)}">{html.escape(c)}</button>' for c in CATEGORIES)
    cards = "\n".join(render_card(a) for a in articles)
    content = f"""
<section class=\"hero\">
  <div>
    <div class=\"kicker\">Agent-maintained AI research publication</div>
    <h1>Dense research notes, daily intelligence, and paper-to-product synthesis.</h1>
    <p class=\"lede\">A Gwern-inspired long-form research archive crossed with a TuringWire-style briefing desk. Built from Markdown, governed by pull requests, and deployed through GitHub Pages.</p>
  </div>
  <aside class=\"panel\">
    <div class=\"kicker\">Current featured essay</div>
    <h3><a href=\"/ai-research-wire/articles/{featured.slug}/\">{html.escape(featured.title)}</a></h3>
    <p>{html.escape(featured.summary)}</p>
    <div class=\"issue-grid\">
      <div class=\"metric\"><strong>{len(articles)}</strong><span>posts</span></div>
      <div class=\"metric\"><strong>{len(CATEGORIES)}</strong><span>beats</span></div>
      <div class=\"metric\"><strong>PR</strong><span>publishing</span></div>
    </div>
  </aside>
</section>
<section>
  <div class=\"kicker\">Research desk</div>
  <h2>Latest writing</h2>
  <input class=\"search\" data-search type=\"search\" placeholder=\"Search essays, categories, summaries...\" aria-label=\"Search articles\">
  <div class=\"filters\"><button class=\"filter active\" data-filter=\"all\">All</button>{category_buttons}</div>
  <div class=\"article-list\">{cards}</div>
</section>
"""
    return chrome(content, title="AI Research Wire", description="AI research notes, news synthesis, paper-style essays, and research digests.")


def render_card(article: Article) -> str:
    return f"""<article class=\"article-card\" data-article-category=\"{html.escape(article.category)}\">
  <div>
    <h3><a href=\"/ai-research-wire/articles/{article.slug}/\">{html.escape(article.title)}</a></h3>
    <p>{html.escape(article.summary)}</p>
    <div class=\"article-meta\"><span>{html.escape(article.date)}</span><span>•</span><span>{html.escape(article.reading_time)}</span><span>•</span><span class=\"category\">{html.escape(article.category)}</span></div>
  </div>
  <a href=\"/ai-research-wire/articles/{article.slug}/\">Read →</a>
</article>"""


def render_article(article: Article) -> str:
    toc_items = "\n".join(f'<li><a href="#{ident}">{html.escape(text)}</a></li>' for ident, text, level in article.toc if level <= 2)
    sources = "".join(f'<li><a href="{html.escape(s.get("url", "#"))}">{html.escape(s.get("title", s.get("url", "source")))}</a></li>' for s in article.sources)
    source_box = f'<div class="source-box"><strong>Sources</strong><ul>{sources}</ul></div>' if sources else ""
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.title,
        "datePublished": article.date,
        "articleSection": article.category,
        "description": article.summary,
        "url": f"https://agilentic.github.io/ai-research-wire/articles/{article.slug}/",
        "publisher": {"@type": "Organization", "name": "AI Research Wire"},
    }
    json_ld_text = json.dumps(json_ld).replace("</", "<\\/")
    content = f"""
<script type=\"application/ld+json\">{json_ld_text}</script>
<div class=\"article-layout\">
  <main class=\"article-body\">
    <div class=\"article-meta\"><span>{html.escape(article.date)}</span><span>•</span><span>{html.escape(article.reading_time)}</span><span>•</span><span class=\"category\">{html.escape(article.category)}</span></div>
    {article.body_html}
    {source_box}
  </main>
  <aside class=\"toc\"><strong>Contents</strong><ul>{toc_items}</ul></aside>
</div>
"""
    return chrome(content, title=f"{article.title} — AI Research Wire", description=article.summary, url_path=f"articles/{article.slug}")


def render_feed(articles: list[Article]) -> str:
    items = "\n".join(f"""<item><title>{html.escape(a.title)}</title><link>https://agilentic.github.io/ai-research-wire/articles/{a.slug}/</link><guid>https://agilentic.github.io/ai-research-wire/articles/{a.slug}/</guid><description>{html.escape(a.summary)}</description><pubDate>{datetime.fromisoformat(a.date).strftime('%a, %d %b %Y 00:00:00 +0000')}</pubDate></item>""" for a in articles)
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
<rss version=\"2.0\"><channel><title>AI Research Wire</title><link>https://agilentic.github.io/ai-research-wire/</link><description>AI research notes, news synthesis, paper-style essays, and research digests.</description>{items}</channel></rss>"""


def build() -> None:
    articles = load_articles()
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    (PUBLIC / "articles").mkdir(parents=True)
    shutil.copytree(ASSETS, PUBLIC / "assets")
    (PUBLIC / ".nojekyll").write_text("")
    (PUBLIC / "index.html").write_text(render_home(articles))
    for article in articles:
        out = PUBLIC / "articles" / article.slug
        out.mkdir(parents=True)
        (out / "index.html").write_text(render_article(article))
    (PUBLIC / "feed.xml").write_text(render_feed(articles))
    (PUBLIC / "llms.txt").write_text("AI Research Wire\n\nPurpose: AI research notes, news synthesis, paper-style essays, and research digests.\n\nCanonical source: https://github.com/agilentic/ai-research-wire\n\nArticles:\n" + "\n".join(f"- {a.title}: https://agilentic.github.io/ai-research-wire/articles/{a.slug}/" for a in articles) + "\n")
    (PUBLIC / "knowledge-graph.json").write_text(json.dumps({"site": "AI Research Wire", "categories": CATEGORIES, "articles": [a.__dict__ | {"markdown": None, "body_html": None, "toc": a.toc} for a in articles]}, indent=2, default=str))
    print(f"Built {len(articles)} articles into {PUBLIC}")


if __name__ == "__main__":
    build()
