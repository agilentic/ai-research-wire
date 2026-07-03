---
title: "Why Markdown-first research sites age well"
description: "Markdown keeps research notes portable, reviewable, and automation-friendly while still supporting a polished publication layer."
date: "2026-07-02"
tags: [publishing, markdown, digital-garden, knowledge-systems]
category: "Research Notes"
status: "evergreen"
author: "Agilentic Research"
---

Markdown-first publishing has a simple advantage: the source artifact remains legible even when the rendering stack changes. A repository of plain-text notes can be searched, reviewed in pull requests, transformed into RSS, and mirrored into future tools.

## Design goals

- **Portable source.** Articles live in `research/posts`, not in a proprietary CMS.
- **Inspectable history.** Changes are ordinary commits and pull requests.
- **Static delivery.** The public site requires no live backend server.
- **Automation hooks.** Scripts can rebuild metadata, check frontmatter, and publish on a schedule.

## Publication layer

The publication layer should be attractive but replaceable. Astro provides routes, layouts, and static builds; the research content remains independent enough to migrate to Quartz or another digital-garden system later.
