---
name: seo-sitemap-validator
description: Audit canonical URLs, OpenGraph meta tags, Schema.org JSON-LD, HTML tag balance, and sitemap.xml across all 136 pages on dublinpubcrawl.app. Use before deploying changes or when investigating Google Search Console indexing reports.
---

# SEO & Sitemap Validator Skill

This skill audits all **136 pages** in `dublinpubcrawl.app` to ensure zero broken canonicals, zero `www.` domain leaks, valid `sitemap.xml` entries, and balanced HTML DOM tags.

## What It Checks
1. **`CNAME` Integrity**: Verifies `CNAME` is strictly `dublinpubcrawl.app` (no `www.`).
2. **`sitemap.xml` Completeness**: Ensures all 136 pages (`<loc>https://dublinpubcrawl.app/...</loc>`) are listed and match real files on disk.
3. **Canonical Tag Alignment**: Ensures every HTML file has `<link rel="canonical" href="https://dublinpubcrawl.app/.../">` matching its exact path.
4. **HTML Tag Balance**: Checks open vs. close counts for `<div>`, `<header>`, `<section>`, `<main>`, and `<script>` tags to prevent layout corruption.
5. **Mobile Modal Safety**: Confirms `.modal-mobile-safe` is applied to modal overlays in `index.html`.

## Running the Validator

```bash
python3 /usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/scratch/github_repo/_agents/skills/seo-sitemap-validator/scripts/validate_seo.py
```

### Exit Codes
- `0`: All 136 pages passed SEO, canonical, and HTML tag balance checks.
- `1`: One or more validation errors detected (blocks deployment).
