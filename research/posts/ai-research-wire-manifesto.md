---
title: AI Research Wire Manifesto
slug: ai-research-wire-manifesto
date: 2026-07-02
category: agentic workflows
status: published
---

# AI Research Wire Manifesto

AI Research Wire is designed as a research-native publication: fast like a static site, dense like a personal knowledge base, and structured enough for agents to maintain it through pull requests.

The editorial model borrows two useful ideas. From Gwern.net, it borrows long-form essays, careful linking, source trails, marginal notes, and the assumption that the best writing gets more valuable as it accumulates context. From TuringWire, it borrows publication discipline: recurring briefings, categories, feeds, structured data, and a public surface that feels current.

## Operating principles

1. GitHub is the source of truth. Every article, metadata edit, workflow change, and design change is reviewable as a diff.
2. Markdown is the durable writing format. Research essays live in `research/posts/*.md` and can be edited by humans or Hermes.
3. Metadata is explicit. `data/articles.json` controls listings, categories, summaries, featured posts, dates, and source links.
4. Publishing is automated but not opaque. GitHub Actions builds the site and deploys to GitHub Pages. Scheduled jobs can run without introducing a hidden CMS.
5. Agents use branches and pull requests. Hermes can research a topic from Telegram, create a Markdown post, update metadata, run checks, push a branch, and open a draft PR.

## Content taxonomy

The initial categories are deliberately editorial, not merely technical:

- AI labs
- Model releases
- Agentic workflows
- Scientific papers
- Infra
- Safety
- Startups

This gives the site enough structure to support daily news synthesis while still supporting evergreen essays.

## Reader experience

The interface should feel like a research desk rather than a marketing page. The homepage emphasizes readable summaries, category filters, recent work, and a strong featured essay. Article pages prioritize typography, footnotes, source links, and a generated table of contents.

## Agent workflow

When Michael asks Hermes in Telegram to research a topic, Hermes should:

1. Research the topic with cited sources.
2. Create a new Markdown essay under `research/posts/`.
3. Add or update the matching record in `data/articles.json`.
4. Run `python scripts/build_site.py` and checks.
5. Create a branch, rebase on `main`, push, and open a draft PR.

This keeps automation powerful but reviewable.
