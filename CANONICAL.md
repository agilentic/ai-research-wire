# Canonical Combined Repository

This repository is preserved as the Agilentic AI Research Wire source.

The combined/canonical AI research website repository is now:

- https://github.com/kitmike/ai-research-os
- https://kitmike.github.io/ai-research-os/

Synchronization model:

- `agilentic/ai-research-wire` remains the upstream source for the Astro/news-wire implementation and historical generated AI-news briefs.
- `kitmike/ai-research-os` imports this repository under `sources/agilentic-ai-research-wire/` using `git subtree` and summarizes its article index in `data/agilentic_articles.json`.
- Future cross-account synchronization should preserve this repo; do not delete or force-push over it.
