# AI Research Wire

Public, Markdown-first AI research publication for Agilentic.

- Live site: <https://agilentic.github.io/ai-research-wire/>
- Source articles: [`research/posts`](research/posts)
- Search index: [`data/articles.json`](data/articles.json)

## Publish a new article

1. Create a Markdown file in `research/posts/my-article-slug.md`.
2. Include frontmatter:

```yaml
---
title: "Article title"
description: "One-sentence abstract."
date: "2026-07-03"
tags: [agents, evaluation]
category: "Research Notes"
status: "note"
author: "Agilentic Research"
---
```

3. Run:

```bash
python3 scripts/build_site.py
npm run build
```

4. Commit and push. GitHub Actions deploys the static site to Pages.

## Local development

```bash
npm ci
npm run dev
```

## AI news automation

The site now includes an automated AI-news publishing loop:

```bash
python3 scripts/update_ai_news.py --max-items 12 --per-source-limit 4
python3 scripts/build_site.py
npm run build
```

- Feed sources live in [`data/ai_news_sources.json`](data/ai_news_sources.json).
- Generated briefs are committed as dated Markdown files: `research/posts/ai-news-wire-YYYY-MM-DD.md`.
- `.github/workflows/ai-news.yml` runs twice daily on GitHub Actions and can also be triggered manually.

## Deployment

- `.github/workflows/pages.yml` builds and deploys to GitHub Pages on pushes to `main`.
- `.github/workflows/publish.yml` runs on a schedule and can also be triggered manually to refresh generated article metadata.
- `.github/workflows/ai-news.yml` fetches public AI-news feeds, commits a fresh Markdown brief, and lets the Pages workflow publish it.
